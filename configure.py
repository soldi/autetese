#!/usr/bin/python
# -*- coding: utf-8 -*

from random import randint
from xml.dom.minidom import parse
import xml.dom.minidom
import shutil
import argparse
import os
import re


def xml_parsing():
  DOMTree = xml.dom.minidom.parse(os.path.abspath(xml_name))
  complete_folder_path = os.path.abspath(folder)
  log_folder_path = "%s/log" % epos_path

  try: 
    shutil.rmtree(complete_folder_path)
  except:
    pass

  try:
    shutil.rmtree(log_folder_path)
  except:
    pass
  os.makedirs(log_folder_path)
  os.makedirs(complete_folder_path)
  test_tag = DOMTree.getElementsByTagName("test")[0]
  app_tags = test_tag.getElementsByTagName("application")

  for app_tag in app_tags:
    app_name = None
    debug_filepath = None

    if app_tag.hasAttribute("name"):
      app_name = app_tag.getAttribute("name")

    configs = app_tag.getElementsByTagName("configuration")
    if len(configs) > 0:
      debug_tag = configs[0].getElementsByTagName("debug")
      debug = len(debug_tag) > 0
      if debug:
        debug_filepath_tag = debug_tag[0].getElementsByTagName("path")
        if len(debug_filepath_tag) > 0:
          debug_filepath = os.path.abspath(debug_filepath_tag[0].childNodes[0].data)
          debug_filepath = debug_filepath.replace("/", "\/");
      options = []
      options_map = {}
      traits = configs[0].getElementsByTagName("trait")
      values = []

      for trait_tag in traits:
        trait_id = trait_tag.getAttribute("id")
        trait_scope = trait_tag.getAttribute("scope")
        value_tags = trait_tag.getElementsByTagName("value")
        # Temos que nos preocupar com o tipos (int, boolean, etc) mais tarde
        values = map(lambda x: x.childNodes[0].data, value_tags)

        if len(values) < 1:
          min_tag = trait_tag.getElementsByTagName("min")
          if len(min_tag) > 0:
            minimum = int(trait_tag.getElementsByTagName("min")[0].childNodes[0].data)
            maximum = int(trait_tag.getElementsByTagName("max")[0].childNodes[0].data)
            values = map(lambda x: str(x), range(minimum, maximum + 1))
   
        if len(values) < 1:
          #for i in range(1, randint(0, 100)):
          for i in range(1, 10):
            values.append(str(randint(0, 1000)))
        
        # Output
        key = (trait_scope.lower() + '_' if trait_scope else '') + trait_id.lower()
        options_map[key] = (trait_scope, values)
        options.append('%s_options=(%s);' % (key, ' '.join(set(values))))

      with open('%s/autetese_%s.sh' % (folder, app_name), 'a') as f:
        f.write('#!/bin/bash\n')
        f.write('EPOS_DIR=%s\n' % epos_path)
#        f.write('START=`date +%H:%M`\n')
        f.write('email_body=$EPOS_DIR/report.log \n')
        map(lambda o: f.write('%s\n' % o), options)
        f.write('failure=0; \nsuccess=0;\n\n')

        f.write('cd $EPOS_DIR \n\n')
        f.write('grep -q -F "automated_test" makefile ||')
        f.write(""" echo "\n\nautomated_test:\n\t\\$(INSTALL) \\$(SRC)/abstraction/\\$(APPLICATION).cc \\$(APP)\n\t\\$(INSTALL) \\$(SRC)/abstraction/\\$(APPLICATION)_traits.h \\$(APP)\n\t\\$(MAKETEST) APPLICATION=\\$(APPLICATION) prebuild_\\$(APPLICATION) clean1 all1 posbuild_\\$(APPLICATION) prerun_\\$(APPLICATION) run1 posbuild_\\$(APPLICATION)\n\t\\$(CLEAN) \\$(APP)/\\$(APPLICATION)*\n" >> makefile\n""")
          
        f.write('sed -i "s/\\$(MACH_PC)_CC_FLAGS.*/\\$(MACH_PC)_CC_FLAGS     := -ggdb -Wa,--32/g" makedefs \n\n')

        f.write('echo "= = = = = TEST REPORT = = = = =" >> ${email_body}\n')
        f.write('echo "= Configurations =">> ${email_body}\n')
        map(lambda k: f.write('echo "%s: %s" >> ${email_body}\n' % (k, ', '.join(options_map[k][1]))), options_map)

        f.write('cd $EPOS_DIR/src/abstraction \n\n')
        f.write('for test_file in ')
        if app_name:
          f.write('%s.cc\n' % app_name)
        else:
          f.write('*_test.cc \n')
        f.write("""do \n\tapplication=`echo ${test_file} | cut -d'.' -f 1` \n\ttrait=`echo ${application}_traits.h`\n\tfailure=0\n\tsuccess=0\n\techo "${application}_traits.h"\n """)
        f.write('\tcp ${application}.cc ${application}.cc.bkp\n')
        f.write("""\tsed -i '/main()/,/return *;*}/ {s/return/cout << "****AUTETESE - test successful" <<endl;return/g}' ${application}.cc \n\tif [ -e $trait ]; then \n\t\tcp ${trait} ${trait}.bkp \n\telse \n\t\t cp ../../include/system/traits.h ${application}_traits.h \n\tfi \n""")

        count = 0
        for key in options_map:
          count += 1
          f.write('%sfor %s in "${%s_options[@]}" \n' % ('\t' * count, key.lower(), key.lower()))
          f.write('%sdo \n' % ('\t' * count))

          if options_map[key][0]:
            f.write('\t%ssed -i "/Traits<%s>: /,// {s/^\\([a-zA-Z0-9[:space:]]*%s[[:space:]]*=[[:space:]]*\\).*\\$/\\1$%s;/g}" $trait \n\n' % ('\t' * count, options_map[key][0], key, key.lower()))
          else:
            f.write('\t%ssed -i "s/static const unsigned int %s.*/static const unsigned int %s = $%s;/g" $trait \n' % ('\t' * count, key, key, key.lower()))
            f.write('\t%ssed -i "s/static const int %s.*/static const int %s = $%s;/g" $trait \n' % ('\t' * count, key, key, key.lower()))
      
        f.write('\t%secho "= Application:${application}"\n' % ('\t' * count))
        f.write('\t%secho "' % ('\t' * count))
        map(lambda k: f.write('%s: $%s ' % (k, k.lower())), options_map)
        f.write('"\n')

        f.write('\t%slog_name=${application}'% ('\t' * count))
        map(lambda k: f.write('_%s_${%s}' % (k, k.lower())), options_map)
        f.write('.log\n')

        f.write('\t%scd $EPOS_DIR\n'% ('\t' * count))

        f.write('\t%smake automated_test APPLICATION=${application} 3>&1 1>>log/${log_name} 2>&1\n'% ('\t' * count))

        f.write("\t%sif grep -q '****AUTETESE - test successful' log/${log_name}; then\n"% ('\t' * count))
        f.write('\t\t%ssuccess=$((success+1))\n'% ('\t' * count))
        f.write('\t\t%smv log/${log_name} log/_success_${log_name}\n'% ('\t' * count))
        f.write('\t%selse\n'% ('\t' * count))
        f.write('\t\t%sfailure=$((failure+1))\n'% ('\t' * count))
  
        if debug:
          if debug_filepath:       
            f.write("""\t\t%ssed -i 's/$(DEBUGGER) $(APP)\/$(APPLICATION)/$(DEBUGGER) \-x "%s" $(APP)\/$(APPLICATION)/' $EPOS_DIR/img/makefile\n""" % ('\t' * count, debug_filepath))

          f.write('\t\t%scp $EPOS_DIR/src/abstraction/${trait} $EPOS_DIR/app/${trait}\n'% ('\t' * count))
          f.write('\t\t%scp $EPOS_DIR/src/abstraction/${application}.cc $EPOS_DIR/app/${application}.cc\n'% ('\t' * count))
          f.write('\t\t%smake debug APPLICATION=${application}\n'% ('\t' * count))
          f.write('\t\t%srm $EPOS_DIR/app/${trait} \n'% ('\t' * count))
          f.write('\t\t%srm $EPOS_DIR/app/${application}.cc\n'% ('\t' * count))

          if debug_filepath:            
            f.write("\t\t%ssed -i 's/$(DEBUGGER) \-x %s $(APP)\/$(APPLICATION)/$(DEBUGGER) $(APP)\/$(APPLICATION)/' $EPOS_DIR/img/makefile\n" % ('\t' * count, debug_filepath))
    
        f.write('\t%sfi\n'% ('\t' * count))

        f.write('\t%scd $EPOS_DIR/src/abstraction\n'% ('\t' * count))

        map(lambda x: f.write('%sdone\n' % ('\t' * x)), reversed(range(1, count + 1)))

        f.write('\techo "= Application: ${application} =">> ${email_body}\n')
        f.write('\techo "Successful tests:${success} - Failed tests:${failure}" >> ${email_body}\n')

        f.write('\tif [ "${failure}" -gt 0 ]; then\n')
        f.write('\t\techo "Failed tests execution log and debugging information on attachment.\n\n" >> ${email_body}\n')
        f.write('\tfi\n')

        f.write('\tcp ${trait}".bkp" ${trait}\n')
        f.write('\trm ${trait}".bkp"\n')
        f.write('\tcp ${application}.cc.bkp ${application}.cc\n')
        f.write('\trm ${application}.cc.bkp\n')
        f.write('done\n')
#        f.write("END=`date +%H:%M`\n")
#        f.write('diff=$(  echo "$END - $START"')
#        f.write(" | sed 's%:%+(1/216000)*%g' | bc -l )\n")
#        f.write('echo "Elapsed time: $diff hours" >> ${email_body}\n')
      f.closed

    else:
      with open('%s/autetese_%s.sh' % (folder, app_name), 'a') as f:
        f.write(random_content(app_name))
      f.closed

# Para escapar o sinal de porcentagem => %%
def random_content(app_name = None):
  app = app_name if app_name else ""  

  return """
cd %s
gnome-terminal --command 
make %s
make | grep warning > original_trace.log

cp include/traits.h include/traits_original.h
echo "--------TEST REPORT--------" >> report.log
echo `grep -m 1 "^APPLICATION " makedefs` >> report.log

for ((total=0;total <100;total++))
    do
        cp include/traits.h include/traits_original.h
        rand_n=$[19+RANDOM %%170]
        echo "ORIGINAL TRAITS LINE = `cat include/traits.h | head -n $rand_n | tail -n 1`" >> report.log
        cat include/traits.h | head -n $rand_n | tail -n 1| grep false
        if [$? =="1"]; then
            sed -i "$rand_n s/= false/= true/" include/traits.h
       else
            sed -i "$rand_n s/= true/= false/" include/traits.h
        fi
echo "MODIFYED TRAITS LINE = $rand_n `cat include/traits.h | head -n $rand_n | tail -n 1`" >> report.log

echo "------------------ COMPILING ERRORS " >> report.log
make %s
make | grep warning > test_trace.log

"----OK"
cp include/traits_original.h include/traits.h
done

echo "END"
""" % (epos_path, app, app)

      
  
if __name__ == "__main__":

  global xml_name
  global epos_path
  global folder

  parser = argparse.ArgumentParser(description='Process XML file and outputs AUTETESE scripts.')
  parser.add_argument('--filename', required=True, help='The XML configuration filename (with the .xml extension).')
  parser.add_argument('--epospath', required=True, help='The absolute path for EPOS.')
  parser.add_argument('--execute', default=False, action='store_true', help='Execute AUTETESE scripts after configuration.')

  args = parser.parse_args()
  xml_name = args.filename
  epos_path = args.epospath
  folder = xml_name[:-4]

  xml_parsing()
  if(args.execute):
    os.system("for script in `ls %s`; do sh %s/$script ; done" % (folder, folder))