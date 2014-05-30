
import os
import xml.etree.ElementTree as ElementTree

import batchelor
import tempfile


def submoduleIdentifier():
	return "gridka"


def submitJob(config, command, outputFile, jobName):
	(fileDescriptor, fileName) = tempfile.mkstemp()
	os.close(fileDescriptor)
	batchelor.runCommand("cp " + batchelor._getRealPath(config.get(submoduleIdentifier(), "header_file")) + " " + fileName)
	with open(fileName, 'a') as scriptFile:
		scriptFile.write(command)
	cmnd = "qsub "
	cmnd += "-j y "
	cmnd += "" if jobName is None else ("-N " + jobName + " ")
	cmnd += "-o " + outputFile + " "
	cmnd += "-P " + config.get(submoduleIdentifier(), "project") + " "
	cmnd += "-q " + config.get(submoduleIdentifier(), "queue") + " "
	cmnd += "-l h_vmem=" + config.get(submoduleIdentifier(), "memory") + " "
	cmnd += "< " + fileName
	(returncode, stdout, stderr) = batchelor.runCommand(cmnd)
	if returncode != 0:
		raise batchelor.BatchelorException("qsub failed (stderr: '" + stderr + "')")
	# example output: "Your job 1601905 ("J2415c980b8") has been submitted"
	jobId = stdout.lstrip("Your job ")
	jobId = jobId[:jobId.find(' ')]
	try:
		jobId = int(jobId)
	except ValueError:
		raise batchelor.BatchelorException('parsing of qsub output to get job id failed.')
	batchelor.runCommand('rm -f ' + fileName)
	return jobId


def getListOfActiveJobs(jobName):
	if jobName is None:
		command = "qstat"
		(returncode, stdout, stderr) = batchelor.runCommand(command)
		if returncode != 0:
			raise batchelor.BatchelorException("qstat failed")
		if stdout == "":
			return []
		jobList = stdout.split('\n')[2:]
		try:
			return [ int(job[:job.find(' ')]) for job in jobList ]
		except ValueError:
			raise batchelor.BatchelorException("parsing of qstat output to get job id failed.")
	command = "qstat -j " + jobName
	(returncode, stdout, stderr) = batchelor.runCommand(command)
	if returncode != 0:
		if stderr and stderr.split('\n')[0][:-1] == "Following jobs do not exist or permissions are not sufficient:":
			return []
		raise batchelor.BatchelorException("qstat failed")
	command = "qstat -xml -j " + jobName
	(returncode, stdout, stderr) = batchelor.runCommand(command)
	if stdout == "" and stderr == "":
		return 0
	root = ElementTree.fromstring(stdout)
	jobIds = []
	for child in root[0]:
		jobIdList = child.findall("JB_job_number")
		if len(jobIdList) != 1:
			raise batchelor.BatchelorException("parsing xml from qstat failed")
		try:
			jobId = int(jobIdList[0].text)
		except ValueError:
			raise batchelor.BatchelorException("parsing int from xml from qstat failed")
		jobIds.append(jobId)
	return jobIds


def getNActiveJobs(jobName):
	return len(getListOfActiveJobs(jobName))


def jobStillRunning(jobId):
	if jobId in getListOfActiveJobs(str(jobId)):
		return True
	else:
		return False
