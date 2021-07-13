#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################
## Purpose of this script is to extract all functions and
## types from ADD .txt file into separate files.
##
## Project: ACAS Xu/Xa/Xo
## Source: PDF version of Algorithm Design Description of the
##         Airborne Collision Avoidance System X document
## Usage: 
## Copy paste all text from .pdf straight to .txt and save it in UTF-8 format.
## That way broken or missing lines can be avoided.
##
## Run: 
## python ConvertADDtxtToJuliaFiles.py ACAS_ADU_18_001_V4R1.txt
##
## Txt file should be complete and must include sections
## List of Algorithms and List of Types.
##
## Note: Developed in Python 2.7.13 32bit
## Creator: Ondrej MICHAL
## Last update: 07/2018
###############################################################

# pylint: disable=C0111, C0103, C0301, C0325

# Global context params
GC = [
    'own.',
    'target_db',
    'modecIntervals',
    'hyp_track_db']

class ffile(object):
    """
    Class encapsuling each function/type.
    """
    name = ''
    fileName = ''
    folder = ''
    content = ''
    dirPath = '' # complete dir path
    usedFnc = []
    useThis = False
    thisParam = '' # STM/TRM

    def __CheckForThis(self):
        for l in self.content:
            if l.find('this.') > -1:
                return True
        return False

    # Remove Myself From Used Functions
    def __RMFUF(self, usedF):
        if self.name in usedF:
            usedF.remove(self.name)
        return usedF

    def __CheckFolderType(self):
        if self.useThis and (self.folder == 'STM' or self.folder == 'TRM'):
            return self.folder
        return ''

    def __init__(self, file_name, fl, pth, used_f, cont):
        self.name = file_name[:-3]
        self.fileName = file_name
        self.folder = fl
        self.dirPath = pth
        self.usedFnc = self.__RMFUF(used_f)
        self.content = cont
        self.useThis = self.__CheckForThis()
        self.thisParam = self.__CheckFolderType()

def ParseCommandLine(args=None):
    from argparse import ArgumentParser

    root = ArgumentParser(
        usage='python ConvertADDtxtToJuliaFiles.py ACAS_ADU_18_001_V4R1.txt',
        description='Complete ADD Julia algorithms extraction and generation of Julia code files.',
        epilog='If updating this script, please consider sharing it among other projects like UMA, ADDA etc.')

    root.add_argument(
        'FileName',
        nargs=1,
        metavar='FileName',
        type=str,
        help="""Txt version of Algorithm Design Description of the Airborne Collision Avoidance System X document.
                Copy paste all text from .pdf straight to .txt and save it in UTF-8 format.
                That way broken or missing lines can be avoided.
                Txt file should be complete and must include sections List of Algorithms and List of Types.""")
    return root.parse_args(args)

def LineTransformParamsCall(line):
    from re import search

    # Bug fix. 'params' should be followed by '().', not '.'
    line = line.replace('params.', 'params().')

    replacement = "this.params"
    pattern_ = search(r'(?<=params\(\)),.*', line)
    pattern = search(r'(?<=params\(\)).*', line)

    if pattern_:
        line = line.replace('params()', replacement)
    elif pattern:
        fin_patt = pattern.group().split(')')[0]
        param_groups = fin_patt.strip('.').split('.')
        for param_name in param_groups:
            param_name = param_name.lstrip(',')
            param_name = param_name.strip()
            mode_ptrn = search(r'\[.*\]', param_name)
            if mode_ptrn:
                replacement += '["' + param_name.replace(mode_ptrn.group(), '') + '"]'
                replacement += mode_ptrn.group()
            elif ')' in param_name:
                param_name_ = param_name.rstrip(')')
                param_name_ = param_name_.rstrip()
                replacement += '["' + param_name_ + '"])'
            elif ';' in param_name:
                param_name_ = param_name.rstrip(';')
                param_name_ = param_name_.rstrip()
                replacement += '["' + param_name_ + '"];'
            else:
                replacement += '["' + param_name + '"]'
        line = line.replace('params()' + fin_patt, replacement)
    return line

def AddThisToGC(line):
    from re import finditer

    for gc in GC:
        pattern = r'[^.\w]' + gc
        pattern = pattern.replace(r'.', r'\.')
        for p in finditer(pattern, line):
            p_ = p.group().replace(gc, 'this.' + gc)
            line = line.replace(p.group(), p_)
    return line

def ClearBrackets(line):

    line = line.replace('( ', '(')
    line = line.replace(' )', ')')
    return line

def RemoveCR(originalCode):
    """Remove carriage return (CR) from lines."""
    from re import search

    for l in range(len(originalCode)):
        line = originalCode[l]
        if search('\S+\r\S+', line):
            originalCode[l] = ' '.join(line.splitlines())
    return originalCode

def GetNextLines(origCode, idx):

    lineVect = []
    for i in range(idx + 1, len(origCode)):
        if len(origCode[i].split()) < 1:
            break
        elif origCode[i].split()[0].isdigit():
            break
        else:
            lineVect.append(origCode[i])
    return lineVect

def JoinLines(line, nextL):
    from re import match

    if not line.split()[0].isdigit() or 'end' in line.split():
        return line

    if not match(r'\s*\d+\s+', line):
        line += ' '
    for l in nextL:
        if SkipHeaderFooter(l) or 'Referenced In:' in l:
            return line
        if not l.split()[0].isdigit():
            line = line.rstrip('\n')
            #line += l.strip()
            line = line+" "+l.strip()
    return line

def SeparateLines(line):

    line_v = []
    splitWords = line.split()
    if splitWords[0].isdigit():
        line_no = int(splitWords[0])
        line_no = str(line_no + 1)
        if line_no in splitWords:
            tmp_line = ''
            for wrd in splitWords:
                if wrd == line_no:
                    line_v.append(tmp_line+'\n')
                    tmp_line = wrd
                    line_no = str(int(line_no) + 1)
                else:
                    tmp_line = tmp_line + ' ' + wrd
            line_v.append(tmp_line+'\n')
        else:
            line_v.append(line)
    return line_v

def SkipHeaderFooter(line):

    if ('ACAS_AD' in line or 'Algorithm Design Description' in line):
        return True
    return False

def CheckEnds(line, noOfEnds):

    AddEnd = ['function', 'for', 'if', 'while', 'type']
    _li = line.split()
    if _li:
        if _li[0] in AddEnd:
            noOfEnds += 1
        elif _li[0] == 'end':
            noOfEnds -= 1

    return noOfEnds

def CheckForUsedFncs(line, pureAlgos):
    from re import search

    usedFncs = []
    for a in pureAlgos:
        idx = 0
        start = 0
        while idx > -1:
            idx = line.find(a, start)
            if idx > -1:
                if search(r'(^|\s|[^\w\:\{])' + a + r'\(', line):
                    usedFncs.append(a)
                start = idx + 1
    return usedFncs

def ConvertLine(line):
    from re import sub

    # remove reference tags
    line = sub(r'\(p\. \d+\)', '', line)
    line = sub(r'\(p\. E-\d+\)', '', line)
    # remove leading line numbers
    line = sub(r'^\s*\d+', '', line)
    # remove other alpahetical malformation
    line = sub(r'^D\s*', '', line)
    line = sub(r'^RA\s*', '', line)
    #line = sub(r'\s*FT\s*', '', line)
    # remove empty lines
    line = sub(r'^\s*$', '', line)
    # correct apostrophe
    line = sub("’", "'", line)
    line = sub("\x92", "'", line)
    line = sub("\x91", "'", line)
    line = sub("\x94", "'", line)
    # correct if statement
    line = sub(r'if\(', r'if (', line)
    # remove dash
    line = sub(r'\s*-\s*$', '', line)
    line = sub(r'\_\-\s*', '_', line)
    # remove globals
    for g in GC:
        if 'global {}'.format(g) in line:
            line = ''

    line = LineTransformParamsCall(line)
    line = AddThisToGC(line)
    line = ClearBrackets(line)

    return line

def Indent(line, indent):
    """ Correct indentation """
    from re import match

    indentAdd = ['function', 'for', 'if', 'elseif', 'else', 'while', 'type']
    indentRem = ['end', 'elseif', 'else']

    line = line.strip()

    for i in indentRem:
        if match(r'^(\s)*' + i + r'(\s|\Z)', line):
            indent -= 4
            break

    line = line.rjust(len(line) + indent)

    for j in indentAdd:
        if match(r'^(\s)*' + j + r'(\s|\Z)', line):
            indent += 4
            break

    if indent < 0:
        raise RuntimeError
    return(line, indent)

def GetFileName(line):
    """Add postfix to function name creating a file name."""
    
    fileName = line[line.rfind(' ') + 1:]
    return fileName.rstrip('\t\n\r\f\v') + '.jl'

def AnalyzeFirstParam(db, fncList):
    """Analyze if this::STM/TRM needs to be added."""
    
    if not fncList or not db:
        raise RuntimeError('Missing functions.')

    while True:
        counter = 0
        for i in fncList:
            for j in db[i].usedFnc:
                # upwards logic
                if db[j].useThis and not db[i].useThis:
                    db[i].useThis = True
                    counter += 1
                if db[j].thisParam and not db[i].thisParam:
                    db[i].thisParam = db[j].thisParam
                    counter += 1
                # downwards logic
                if db[i].thisParam and db[j].useThis and not db[j].thisParam:
                    db[j].thisParam = db[i].thisParam
                    counter += 1
        if counter == 0:
            break
    return db

def AddThisToFncs(db):
    """Add 'this::' to first line or 'this' to any other line."""
    from re import finditer

    for i in db:
        if db[i].thisParam and not db[i].useThis:
            print('ERROR: Missing params in fnc: {}.'.format(db[i].name))
            print('thisParam: {}, useThis: {}'.format(db[i].thisParam, db[i].useThis))
            raise RuntimeError

        for y in range(len(db[i].content)):
            if db[i].useThis and db[i].thisParam:
                if db[i].name + '()' in db[i].content[y]:
                    db[i].content[y] = db[i].content[y].replace(db[i].name + '(', db[i].name + '(this::' + db[i].thisParam)
                elif db[i].name + '(' in db[i].content[y]:
                    db[i].content[y] = db[i].content[y].replace(db[i].name + '(', db[i].name + '(this::' + db[i].thisParam + ', ')
            for fn in db[i].usedFnc:
                if db[fn].useThis:
                    for p in finditer(r'(^|\s|[^\w\:\{])' + fn + r'\(\s*\)*', db[i].content[y]):
                        p_ = ''
                        if '()' in p.group():
                            p_ = p.group().replace(fn + '()', fn + '(this)')
                        elif '( ' in p.group():
                            p_ = p.group().replace(fn + '( ', fn + '(this,')
                        elif '(' in p.group():
                            p_ = p.group().replace(fn + '(', fn + '(this, ')
                        db[i].content[y] = db[i].content[y].replace(p.group(), p_)
    return db

def PrintData(db):
    """
    Print data stored in ffile classes.
    Add '>results.txt' into commandline for file output.
    """
    
    for i in db:
        #print(db[i].name)
        #print(db[i].useThis, db[i].thisParam)
        #print(db[i].usedFnc)
        #useIt = []
        #for y in db[i].usedFnc:
        #    useIt.append(db[y].useThis)
        #print(useIt)
        for l in db[i].content:
            print(l)
        #print('\n---New Function---\n')

def GenFiles(db):
    """Generate files into folders."""
    import os

    for i in db:
        if os.getcwd() != db[i].dirPath:
            os.chdir(db[i].dirPath)
        with open(db[i].fileName, 'w') as newFile:
            for line in db[i].content:
                newFile.write(line + '\n')
            newFile.close()

def ListAllFiles():
    """
    Generate list of all files in ACAS_Xu folder with 'include(' prefix.
    Dont forget to add: ACAS_Xu.jl, Aliases.jl, and paramsfile_type.jl.
    """
    import os

    os.chdir('..')
    CWD = os.getcwd()
    listDir = os.listdir(CWD)
    fileDB = [] #file database

    for i in listDir:
        if i[-3:] != '.jl':
            fileDB.append('include("{}")'.format(i))
        else:
            flDir = os.listdir(os.path.join(CWD, i))
            for y in flDir:
                fileDB.append('include("{}/{}")'.format(i, y))

    with open('IncFileList.txt', 'w') as incFileList:
        for l in fileDB:
            incFileList.write(l + '\n')
    incFileList.close()

if __name__ == '__main__':
    import os
    from re import match

    ### User settings
    # Root folder
    root_f = 'ACAS_Xu_R0'
    # Set correct chapter for the document
    # Files will be sorted into folders acc. to chapters
    chapters = {
        '2 Surveillance and Tracking Module Description\n' : 'STM',
        '3 Threat Resolution Module Description\n' : 'TRM',
        'A STM Housekeeping\n' : 'STMHousekeeping',
        'B Mode C Processing Implementation\n' : 'ModeCProcessingImplementation',
        'C Correlation Processing Implementation\n' : 'CorrelationProcessingImplementation',
        'D Constant Variables\n' : 'ConstantVariables',
        'E Data Structure Definitions\n' : 'DataStructures',
        'G Data Table Format Specification\n' : 'DataTableFormatSpecification',
        'H Math Utilities\n' : 'MathUtilities',
        'I Data Management Utilities\n' : 'DataManagementUtilities',
        'J Julia Standard Library Functions\n' : 'JuliaStandardLibraryFunctions'}

    parameters = ParseCommandLine()
    pureAlgos = []
    lineVec = []
    usedFnc = []
    newFnc = False
    emptyLine = False
    RecordAllAlgorithms = False
    newFileName = ''
    dirPath = ''
    indent = 0
    noOfEnds = 0
    cwd = os.getcwd()
    ft_db = {}

    if not os.path.exists(root_f):
        os.makedirs(root_f)

    for ch in chapters:
        dirPath = os.path.join(root_f, chapters.get(ch))
        if not os.path.exists(dirPath):
            os.makedirs(dirPath)

    with open(parameters.FileName[0]) as codeFile:
        originalCode = codeFile.readlines()

        line = ''
        nextLine = ''
        originalCode = RemoveCR(originalCode)
        for idx in range(len(originalCode) - 1):

            line = originalCode[idx]

            if SkipHeaderFooter(line):
                continue

            # start of algorithm listing
            if 'LIST OF ALGORITHMS' in line:
                RecordAllAlgorithms = True
            # end of algorithm listing
            elif 'LIST OF TYPES' in line:
                RecordAllAlgorithms = False
            # make lists of algorithms
            if RecordAllAlgorithms and match(r'\d+\s+\w+\s+\d+', line):
                pureAlgos.append(line.split()[1])
                continue

            # set designated directory
            if line in chapters:
                dirPath = os.path.join(cwd, root_f, chapters.get(line))

            # create file name for new function
            if match(r'Algorithm\s+\d+\s+\w+', line):
                fName = line.split()[2]
                newFileName = GetFileName(fName)

            # create file name for new type
            elif match(r'Type\s+\d+\s+\|\s+\w+', line):
                fName = line.split()[3]
                newFileName = GetFileName(fName)

            # find lines starting with:
            # '1 function', '1 type' or '1 abstract'
            if (match(r'\s*1\s+function', line) or match(r'\s*1\s+type', line) or match(r'\s*1\s+abstract', line)):
                newFnc = True

            # if line is empty, skip next step
            emptyLine = match(r'^\s*$', line)

            # remove references to pages and other garbage
            if not emptyLine and newFnc:
                nextLine = GetNextLines(originalCode, idx)
                if nextLine:
                    line = JoinLines(line, nextLine)
                line_vec = SeparateLines(line)
                for li in line_vec:
                    li = ConvertLine(li)
                    noOfEnds = CheckEnds(li, noOfEnds)
                    li, indent = Indent(li, indent)
                    lineVec.append(li)

                    uf = CheckForUsedFncs(line, pureAlgos)
                    for f in uf:
                        if f not in usedFnc:
                            usedFnc.append(f)

            # close function
            if not noOfEnds and newFnc:
                newFnc = False

            # dump function into ffile object
            if not newFnc and lineVec:
                fldr = dirPath[dirPath.rfind('\\') + 1:]
                ft_db[newFileName[:-3]] = ffile(newFileName, fldr, dirPath, usedFnc, lineVec)

                lineVec = []
                usedFnc = []
                indent = 0
                noOfEnds = 0
                newFileName = ""

        ft_db = AnalyzeFirstParam(ft_db, pureAlgos)
        ft_db = AddThisToFncs(ft_db)

        ## Final data can be streamed into files or printed out
        GenFiles(ft_db)
        #PrintData(ft_db)
        #ListAllFiles()
