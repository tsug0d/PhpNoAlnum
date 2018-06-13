import random
import re
import sys
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--file', type=argparse.FileType('r'),
    help="Input php file, please run it first to make sure it is in correct php syntax")
parser.add_argument('--out', type=argparse.FileType('w'),
    help="Specifies Output obfuscated php file")

args = parser.parse_args(sys.argv[1:])

if ('out=None' in str(args)) or ('file=None' in str(args)):
    parser.print_help()
    sys.exit()

def turn_to_string(length):
    return '$%s=@"$%s";'%('_'*length,'_'*length)

def character_present(inp):
    regex="[0-9a-zA-Z]"
    m=re.findall(regex,inp)
    return sorted(list(set(m)))

def pick_array(array):
    return array[random.randint(0,len(array)-1)]

def pick_numb(numb):
    return numb[random.randint(0,len(numb)-1)]

def return_distance(char):
    tmp=ord(char)
    if 49<=tmp<=53:
        return "1-"+str(tmp-ord('1'))
    elif 54<=tmp<=57:
        return "6-"+str(tmp-ord('6'))
    elif 65<=tmp<=79:
        return "A-"+str(tmp-ord('A'))
    elif 80<=tmp<=86:
        return "P-"+str(tmp-ord('P'))
    elif 87<=tmp<=90:
        return "W-"+str(tmp-ord('W'))
    elif 97<=tmp<=111:
        return "a-"+str(tmp-ord('a'))
    elif 112<=tmp<=118:
        return "p-"+str(tmp-ord('p'))
    elif 119<=tmp<=122:
        return "w-"+str(tmp-ord('w'))

def init():
    instructions=[]
    gen_array=['$_=[];']
    gen_numb=['$__=![];','$__=!"";','$__=!\'\';']
    array=pick_array(gen_array)
    numb=pick_numb(gen_numb)
    gen_char_A="$___=@$_[''];"
    gen_char_a="$____=$__;++$____;++$____;$____=$_[$____];"
    gen_char_6="$_=$__;++$_;++$_;++$_;++$_;++$_;$_=@\"$_\";"
    gen_char_P="$_____=$____^$__;"
    gen_char_W="$______=$____^$_;"
    gen_char_p="$_______=$___^$__;"
    gen_char_w="$________=$___^$_;"
    gen_char_0="$_________=$__;--$_________;"
    instructions.append(array)
    instructions.append(turn_to_string(1))
    instructions.append(numb)
    instructions.append(turn_to_string(2))
    instructions.append(gen_char_A)
    instructions.append(gen_char_a)
    instructions.append(gen_char_6)
    instructions.append(gen_char_P)
    instructions.append(gen_char_W)
    instructions.append(gen_char_p)
    instructions.append(gen_char_w)
    instructions.append(gen_char_0)
    instructions.append(turn_to_string(9))
    return instructions

def gen_instruction(char):
    global rand_numb
    global address
    if char in address.keys():
        return ''
    distance=return_distance(char).split('-')
    instruct="$%s=$%s;"%("_"*rand_numb,"_"*address[distance[0]])
    instruct+="++$%s;"%("_"*rand_numb)*int(distance[1])
    if char.isdigit():
        instruct+=turn_to_string(rand_numb)
    address[char]=rand_numb
    rand_numb+=1
    return instruct

def get_key_value(char):
    global address
    if char not in address.keys():
        return char
    return address[char]

def translate_to_php(length):
    if str(length).isdigit():
        return "$%s"%("_"*length)
    return length

def gen_final_instruction(string):
    global tmp
    global rand_numb
    global address
    string=list(string)
    string=map(get_key_value,string)
    string=map(translate_to_php,string)
    final="$%s="%("_"*rand_numb)+".@".join(x for x in string)+";"
    tmp.append("$%s"%("_"*rand_numb))
    rand_numb+=1
    return final

def parse_func(string):
    global tmp
    global rand_numb
    global instructions
    regex="^(?P<func>[A-Za-z0-9_].*)\((?P<value>.*)\)$"
    m=re.match(regex,string)
    function=m.group('func')
    value=m.group('value').replace("'","").replace('"',"")
    if value=='':
        instruction=gen_final_instruction(function)
        instruction+=tmp[0]+'();'
        instructions.append(instruction)
        tmp=[]
    elif value!='' and ',' not in value:
        instruction=gen_final_instruction(function)
        instruction+=gen_final_instruction(value)
        instruction+=tmp[0]+'(%s);'%tmp[1]
        instructions.append(instruction)
        tmp=[]
    else:
        instruction=gen_final_instruction(function)
        test=value.split(',')
        for i in test:
            instruction+=gen_final_instruction(i)
        hold="%s(%s);"%(tmp[0], ','.join(x for x in tmp[1:len(test)+1]))
        instructions.append(instruction)
        instructions.append(hold)
        tmp=[]

def clear_input(string):
    string=string.strip()
    if string.startswith("<?php"):
        string=string[5:]
    if string.startswith("<?="):
        string=string[3:]
    if string.endswith("?>"):
        string=string[:-2]
    string=string.replace("\n","")
    return string

def parse_text(string):
    global rand_numb
    string=string.replace("\n","").strip()
    collect=string.split(';')
    collect=collect[:-1]
    for i in collect:
        parse_func(i)

def safe_output(string):
    dangerous=['-','!','@','#','$','%','^','&','*','(',')','=','+','/','<','>','?','.',',','"','\'','|',';','[',']','{','}',':',' ']
    for i in dangerous:
        string=string.replace('.@%s.'%i,'.\'%s\'.'%i)
        string=string.replace('.@%s.'%i,'.\'%s\'.'%i)
    return string

if __name__ == "__main__":
    tmp=[]
    address={'a':4,'p':7,'w':8,'A':3,'P':5,'W':6,'1':2,'6':1,'0':9}
    instructions=[]
    rand_numb=10;
    instructions=list(init())
    input_php=clear_input(args.file.read())
    input_list=character_present(input_php)
    for i in input_list:
        new_instruct=gen_instruction(i)
        instructions.append(new_instruct)
    parse_text(input_php)
    final_output=''.join(x for x in instructions)
    final_output=safe_output(final_output)
    final_output="<?=\n"+final_output
    args.out.write(final_output)
    print 'Obfuscate Done!'
    print 'Your payload is saved in: ' + args.out.name
