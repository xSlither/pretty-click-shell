Dim wsh, fso
Dim LocalDirectory

Set wsh = CreateObject("WScript.Shell")
LocalDirectory = GetFileDirectory(WScript.ScriptFullName)

Return = wsh.Run(LocalDirectory & "testapp.cmd teststdout > " & LocalDirectory & "output.txt", 0, True)

Dim file, txt

Set fso = CreateObject("Scripting.FileSystemObject")
Set file = fso.OpenTextFile(LocalDirectory & "output.txt", 1)

txt = file.ReadAll
file.Close

Set wsh = Nothing
Set fso = Nothing
Set file = Nothing

MsgBox txt


Function GetFile(str)
	Dim lent, i, s
	lent = Len(str)
	
	For i = 0 To lent
		If Not Mid(str, (lent - i), 1) = "\" Then
			s = Mid(str, (lent - i), 1) & s
		Else
			Exit For
		End If
	Next
	
	GetFile = s
End Function

Function GetFileDirectory(path)
	Dim file, flen
	
	file = GetFile(path)
	flen = Len(file)
	
	GetFileDirectory = Replace(path, file, "")
End Function