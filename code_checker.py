import os
import sys
import filecmp
import re
import subprocess
from subprocess import CalledProcessError, TimeoutExpired
import multiprocessing
from multiprocessing import Process, Queue
import time
STATUS_CODES = {
    200: 'OK',
    201: 'ACCEPTED',
    400: 'WRONG ANSWER',
    401: 'COMPILATION ERROR',
    402: 'RUNTIME ERROR',
    403: 'INVALID FILE',
    404: 'FILE NOT FOUND',
    408: 'TIME LIMIT EXCEEDED'
}


class Program:
    """ Class that handles all the methods of a user program """

    def __init__(self, filename, inputfile, timelimit, expectedoutputfile):
        """Receives a name of a file from the userIt must be a valid c, c++, java file """
        self.fileName = filename  # Full name of the source code file
        self.language = None  # Language
        self.name = None  # File name without extension
        self.inputFile = inputfile  # Input file
        self.expectedOutputFile = expectedoutputfile  # Expected output file
        self.actualOutputFile = "output2.txt"  # Actual output file
        self.timeLimit = timelimit  # Time limit set for execution in seconds

    def isvalidfile(self):
        """ Checks if the filename is valid """
        validfile = re.compile("^(\S+)\.(java|cpp|c|py)$")
        matches = validfile.match(self.fileName)
        if matches:
            self.name, self.language = matches.groups()
            return True
        return True

    def compile(self):
        """ Compiles the given program, returns status code and errors """

        # Remove previous executables
        if os.path.isfile(self.name):
            os.remove(self.name)

        # Check if files are present
        if not os.path.isfile(self.fileName):
            return 404, 'Missing file'

        # Check language
        cmd = None
        print(self.language)
        if self.language == 'java':
            cmd = 'javac {}'.format(self.fileName)
        elif self.language == 'c':
            cmd = 'gcc -o {0} {1}'.format(self.name, self.fileName)
        elif self.language == 'cpp':
            cmd = 'g++ -o {0} {1}'.format(self.name, self.fileName)
        elif self.language == 'py':
            return 200,None
            #cmd = 'python3 {}'.format(self.fileName)

        # Invalid files
        if cmd is None:
            return 403, 'File is of invalid type'

        try:
            print("hi")
            proc = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )

            # Check for errors
            if proc.returncode != 0:
                return 401, proc.stderr
            else:
                return 200, None
        except CalledProcessError as e:
            print(e.output)

    def run(self):
        """ Runs the executable, returns status code and errors """
        print("run")
        # Check if files are present
        if not os.path.isfile(self.fileName) :
            return 404, 'Missing executable file'

        # Check language
        cmd = None
        if self.language == 'java':
            cmd = 'java {}'.format(self.name)
        elif self.language in ['c', 'cpp']:
            cmd = self.name
        elif self.language == 'py':
            #return 200,None
            cmd = 'python3 {}'.format(self.fileName)
        # Invalid files
        if cmd is None:
            return 403, 'File is of invalid type'

        try:
            with open('output2.txt', 'w') as fout:
                fin = None
                if self.inputFile and os.path.isfile(self.inputFile):
                    fin = open(self.inputFile, 'r')
                
                Q=Queue()
                def foo():
                    print ('Starting function')
                    proc = subprocess.run(
                    cmd,
                    stdin=fin,
                    stdout=fout,
                    stderr=subprocess.PIPE,
                    timeout=self.timeLimit,
                    universal_newlines=True,
                    shell=True
                    )
                    Q.put(proc)
                    print ('Finished function')
                    return CalledProcessError

                p = multiprocessing.Process(target=foo)
                print ('Process before execution:', p, p.is_alive())
                p.start()
                print ('Process running:', p, p.is_alive())
                fl = p.is_alive()
                while fl:
                    if fl==False:
                        break
                    
                    time.sleep(3)
                    fl=p.is_alive()
                    if fl==False:
                        proc = Q.get()
                        break
                    p.terminate()
                    print ('Process terminated:', p, p.is_alive())
                    break
                    
                p.join()
                print ('Process joined:', p, p.is_alive())
                print ('Process exit code:', p.exitcode)
                
                try:
                    print(proc)
                except Exception as e:
                    return 400,None

            # Check for errors
            if proc.returncode != 0:
                return 402, proc.stderr
            else:
                return 200, None
        except TimeoutExpired as tle:
            proc.kill()
            return 408, tle
        except CalledProcessError as e:
            print(e.output)

        # Perform cleanup
        if self.language == 'java':
            os.remove('{}.class'.format(self.name))
        elif self.language in ['c', 'cpp']:
            os.remove(self.name)

    def match(self):
        if os.path.isfile(self.actualOutputFile) and os.path.isfile(self.expectedOutputFile):
            result = filecmp.cmp(self.actualOutputFile, self.expectedOutputFile)
            if result:
                return 201, None
            else:
                return 400, None
        else:
            return 404, 'Missing output files'


def codechecker(filename, inputfile=None, expectedoutput=None, timeout=1, check=True):
    newprogram = Program(
        filename=filename,
        inputfile=inputfile,
        timelimit=timeout,
        expectedoutputfile=expectedoutput
    )
    print(filename)
    if newprogram.isvalidfile():
        print('Executing code checker...')
        # Compile program
        compileResult, compileErrors = newprogram.compile()
        print('Compiling... {0}({1})'.format(STATUS_CODES[compileResult], compileResult), flush=True)
        if compileErrors is not None:
            sys.stdout.flush()
            print(compileErrors, file=sys.stderr)
            exit(0)

        # Run program
        runtimeResult, runtimeErrors = newprogram.run()
        print('Running... {0}({1})'.format(STATUS_CODES[runtimeResult], runtimeResult), flush=True)
        if runtimeErrors is not None:
            sys.stdout.flush()
            print(runtimeErrors, file=sys.stderr)
            exit(0)

        if check:
            # Match expected output
            matchResult, matchErrors = newprogram.match()
            print('Verdict... {0}({1})'.format(STATUS_CODES[matchResult], matchResult), flush=True)
            if matchErrors is not None:
                sys.stdout.flush()
                print(matchErrors, file=sys.stderr)
                exit(0)
    else:
        print('FATAL: Invalid file', file=sys.stderr)


#if __name__ == '__main__':

    