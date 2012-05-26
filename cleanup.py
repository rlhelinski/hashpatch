import (hashpatch)

archiveRoot = '/Users/ryan/Archives/Compress/Personal'
myYearMap = hashpatch.sortByYearModified("/Users/ryan/Dropbox/Personal", excludePattern=".*/Private-1\.3\.2/.*")

BackupMap = hashpatch.hashMap()
BackupMap.load('/Users/ryan/TimeMachine-2012-01-28-150538.sha512.bz2')
BackupMap.rootPath = "/Volumes/Time Machine/Backups.backupdb/Emory/2012-01-28-150538/Macintosh HD/Users/ryan"
BackupSubsetMap = BackupMap.makeSubset("/Volumes/Time Machine/Backups.backupdb/Emory/2012-01-28-150538/Macintosh HD/Users/ryan/Downloads")
len (BackupMap)
len (BackupSubsetMap)
DownloadMap = hashpatch.hashMap("/Users/ryan/Downloads")
MissingFiles = hashpatch.checkForMissingInDest(BackupSubsetMap, DownloadMap)
BackupMap.hashDict[MissingFiles[1]]
['/Volumes/Time Machine/Backups.backupdb/Emory/2012-01-28-150538/Macintosh HD/Users/ryan/Downloads/Psychedelic Stereo (320)/04 Julias Labyrinth.mp3', "/Volumes/Time Machine/Backups.backupdb/Emory/2012-01-28-150538/Macintosh HD/Users/ryan/Music/iTunes/iTunes Media/Music/Mimosa/Mimosa - Psychedelic Stereo - Muti052/Julia's Labyrinth.mp3"]
>>> os.path.isfile("/Users/ryan/Downloads/Psychedelic Stereo (320)/04 Julias Labyrinth.mp3")
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
NameError: name 'os' is not defined
>>> import os
>>> os.path.isfile("/Users/ryan/Downloads/Psychedelic Stereo (320)/04 Julias Labyrinth.mp3")
False
>>> os.path.isfile("/Users/ryan/Music/iTunes/iTunes Media/Music/Mimosa/Mimosa - Psychedelic Stereo - Muti052/Julia's Labyrinth.mp3")
# So, I am going through and looking for at least one file to still exist that is missing
BackupBasename = "/Volumes/Time Machine/Backups.backupdb/Emory/2012-01-28-150538/Macintosh HD"
def makeMissingReport(BackupBasename, MissingFiles):
	for key in MissingFiles:
		numExist = 0
		for path in BackupMap.hashDict[key]:
			if (os.path.isfile(path.replace(BackupBasename, ""))):
				numExist += 1
		print base64.b16encode(key) + ":"
		if numExist > 0:
			print "OK, %d files still exist" % numExist
		else:
			print "FAIL, all files with that checksum are missing"

36B9CF8FC06F3BCF558DD497396F660EC7B2C2BE7F2703D363C39352D4CF2C61BFCDC537B2570726C1EDD3BE9E9B721D898D48061618A6BB7C86DB26C147BF8A:
OK, 1 files still exist
D020A6F11159544F371C42699F23146E14168C23FFBD112E253C729F867BA3CB683117C9103A690DCA9880321D9C282819C311098B6A79E979E32F7F8EEE8954:
OK, 1 files still exist
89D95D88662F51216834EB9644A1CDA4A3087892B63AEE4F63AB31CFD54505298B9FBF26F580683CF833E863E0B5D7544E9D9AB03E506330F2935454A58EAA49:
OK, 1 files still exist
5E6079E7ABCCBE141E49FE7351B3D09C7F14B5A478283FB793F0F480A8580DE3621C4FAD337B5D834D050717A9E90CB7C86DE1A87D7F8A4220F0ADB7222577B1:
OK, 1 files still exist
8BF1998F1D7C73BF6616A4907EC1315A18DCB7D6B088E3335B2EC6CDCA0FFC8E72502596BF77A340D42CD17D7D75BDE92A73E7E77A939066A865E81E08D31DE7:
OK, 1 files still exist
9DE04BC260DA90DC5D3CC8A9B75472D8A01C5041064C5B29143F4E48406AD782977869F4473E6FFC827E27D032DBBD4AEC4906405748AAC085DB54B69283B736:
FAIL, all files with that checksum are missing
FF20E87EF3ED4824C551AA5025B96B626C3A963991E1B806C71E72A342977126B4D47242BD6FE7EF84D2F076A70606EA1E57053AAED1DD855FF5C4AAB70C9337:
OK, 1 files still exist
5BDE61EF637A87D0734D2BB6505331B9E769FBA69AD1E690C1BD1C83D351CBADC8DA6185956B288396DBC1C7464C3AA87FEF3771AC5FEAB350063B095B4BFECF:
OK, 1 files still exist
CF83E1357EEFB8BDF1542850D66D8007D620E4050B5715DC83F4A921D36CE9CE47D0D13C5D85F2B0FF8318D2877EEC2F63B931BD47417A81A538327AF927DA3E:
OK, 117 files still exist
1B7409CCF0D5A34D3A77EAABFA9FE27427655BE9297127EE9522AA1BF4046D4F945983678169CB1A7348EDCAC47EF0D9E2C924130E5BCC5F0D94937852C42F1B:
OK, 1 files still exist
>>> BackupMap.hashDict[base64.b16decode("9DE04BC260DA90DC5D3CC8A9B75472D8A01C5041064C5B29143F4E48406AD782977869F4473E6FFC827E27D032DBBD4AEC4906405748AAC085DB54B69283B736")]
['/Volumes/Time Machine/Backups.backupdb/Emory/2012-01-28-150538/Macintosh HD/Users/ryan/Downloads/LOCCS Report Draft 20110614.docx']

key

PicturesMap = hashpatch.hashMap("/Users/ryan/Pictures")
BackupSubsetMap = BackupMap.makeSubset(BackupBasename + "/Users/ryan/Pictures")
MissingFiles = hashpatch.checkForMissingInDest(BackupSubsetMap, PicturesMap, exclude="/Metadata")
hashpatch.makeMissingReport(BackupBasename, BackupSubsetMap, MissingFiles)


MusicMap = hashpatch.hashMap("/Users/ryan/Music")
MusicMap.save()
BackupSubsetMap = BackupMap.makeSubset(BackupBasename + "/Users/ryan/Music")
MissingFiles = hashpatch.checkForMissingInDest(BackupSubsetMap, MusicMap, exclude="")
hashpatch.makeMissingReport(BackupBasename, BackupSubsetMap, MissingFiles)

ArchivesMap = hashpatch.hashMap("/Users/ryan/Archives")
ArchivesMap.save()
BackupSubsetMap = BackupMap.makeSubset(BackupBasename + "/Users/ryan/Archives")
MissingFiles = hashpatch.checkForMissingInDest(BackupSubsetMap, ArchivesMap, exclude="")
hashpatch.makeMissingReport(BackupBasename, BackupSubsetMap, MissingFiles)

# OK, I now have everything sane. I didn't accidentally delete anything. 

ArchivesMap = CurrentMap.makeSubset("/Users/ryan/Archives")
hashpatch.deleteDupsInDest(ArchivesMap, DownloadMap, prompt=True, act=True)
DownloadMap.removeMissing()
#...
CurrentMap.removeMissing()
CurrentMap.save()

>>> DropboxMap = CurrentMap.makeSubset("/Users/ryan/Dropbox")
>>> hashpatch.deleteDupsInDest(DropboxMap, DownloadMap, prompt=True, act=True)

