package main

import "os"

func modes() {
	// ok: go.file-mode-too-permissive
	os.WriteFile("token", nil, 0o600)
	// ok: go.file-mode-too-permissive
	os.WriteFile("run.sh", nil, 0o700)
	// ok: go.file-mode-too-permissive
	os.OpenFile("conf", os.O_CREATE, 0640)
	// ruleid: go.file-mode-too-permissive
	os.WriteFile("conf", nil, 0o604)
	// ruleid: go.file-mode-too-permissive
	os.WriteFile("conf", nil, 0644)
	// ruleid: go.file-mode-too-permissive
	os.Chmod("conf", 0o660)
	// ruleid: go.file-mode-too-permissive
	os.OpenFile("conf", os.O_CREATE, 0o777)
}
