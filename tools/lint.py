import os
import sys
import subprocess

JSLINT_ENABLED = True
CHECK_ILLEGAL_CHAR = True

JSLINT_IGNORED_FILES = {
	'timer/src_tnoodle_resources/tnoodleServerHandler/timer/js/mootools-core-1.4.2.js',
	'timer/src_tnoodle_resources/tnoodleServerHandler/timer/js/mootools-more-1.4.0.1.js',
	'timer/src_tnoodle_resources/tnoodleServerHandler/timer/js/stacktrace.js',
	'mootools/src_tnoodle_resources/tnoodleServerHandler/mootools/mootools-core-1.4.2.js',
	'mootools/src_tnoodle_resources/tnoodleServerHandler/mootools/mootools-more-1.4.0.1.js',
	'mootools/src_tnoodle_resources/tnoodleServerHandler/mootools/powertools-1.1.1.js',

	# TODO - the following really ought to get cleaned up at some point
	'webscrambles/src_tnoodle_resources/tnoodleServerHandler/webscrambles/scramblegen.html',
	'jsracer/ButtonGame.js',
	'jsracer/GameMasterGui.js',
	'jsracer/jquery-1.6.4.js',
	'jsracer/jquery.dateFormat-1.0.js',
	'jsracer/stacktrace.js',
	'jsracer/assert.js',
	'noderacer/mongeesing.js',
	'noderacer/noderacer.js'
}
JSLINT_IGNORED_ERRORS = {
	'type is unnecessary.',
}

UNCOMMITABLE_PHRASES = {
	'<'+'<'+'<',
}

# Stolen from http://stackoverflow.com/questions/898669/how-can-i-detect-if-a-file-is-binary-non-text-in-python
# This should jive with git's definition of binary.
def is_binary(filename):
    """Return true if the given filename is binary.
    @raise EnvironmentError: if the file does not exist or cannot be accessed.
    @attention: found @ http://bytes.com/topic/python/answers/21222-determine-file-type-binary-text on 6/08/2010
    @author: Trent Mick <TrentM@ActiveState.com>
    @author: Jorge Orpinel <jorge@orpinel.com>"""
    if os.path.islink(filename):
        return False
    fin = open(filename, 'rb')
    try:
        CHUNKSIZE = 1024
        while 1:
            chunk = fin.read(CHUNKSIZE)
            if '\0' in chunk: # found null byte
                return True
            if len(chunk) < CHUNKSIZE:
                break # done
    # A-wooo! Mira, python no necesita el "except:". Achis... Que listo es.
    finally:
        fin.close()

    return False

def lint(files):
	failures = []
	for f in files:
		if not os.path.exists(f):
			# This file must have been deleted as part of this commit.
			continue
		fileName, ext = os.path.splitext(f)

		if JSLINT_ENABLED:
			if ext == '.js' or ext == '.html':
				if f in JSLINT_IGNORED_FILES:
					print "Not jslinting %s" % f
				else:
					if os.path.isdir(f):
						continue
					print "jslinting %s" % f
					argv = [ 'java', '-jar', 'lib/jslint4java-1.4.6.jar', f ]
					p = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
					fileLines = file(f).read().split("\n")
					stdout, stderr = p.communicate()
					failedJsLint = False
					for line in stdout.split('\n'):
						parsedError = line.split(":")
						if len(parsedError) != 5:
							if line != '':
								assert False, line + " doesn't contain expected number of :'s"
							continue
						_, fileName, lineNumber, col, error = parsedError
						lineNumber = int(lineNumber)
						if error in JSLINT_IGNORED_ERRORS:
							print "Ignoring error %s" % line
						else:
							error = "%s:%s:%s:%s" % ( f, lineNumber, error, fileLines[lineNumber-1] )
							failures.append(error)
					for lineNumber, line in enumerate(fileLines):
						if "console.log" in line:
							failures.append("%s:%s:Call to console.log.:%s" % (
								f, lineNumber+1, line ))
		
		if CHECK_ILLEGAL_CHAR:
			if is_binary(f):
				#print "Skipping binary file %s" % f
				pass
			else:
				if os.path.islink(f):
					continue
				lines = file(f).read().split("\n")
				for lineNumber, line in enumerate(lines):
					for uncommitablePhrase in UNCOMMITABLE_PHRASES:
						if uncommitablePhrase in line:
							error = "%s:%s:Illegal character.:%s" % ( f, lineNumber+1, line )
							failures.append(error)
	return failures
