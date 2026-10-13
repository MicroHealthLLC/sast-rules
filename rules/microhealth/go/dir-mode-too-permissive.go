package main

import "os"

func dirs() {
	// ok: go.dir-mode-too-permissive
	os.MkdirAll("state", 0o700)
	// ok: go.dir-mode-too-permissive
	os.Mkdir("shared", 0750)
	// ruleid: go.dir-mode-too-permissive
	os.MkdirAll("cache", 0o755)
	// ruleid: go.dir-mode-too-permissive
	os.MkdirAll("spool", 0o2770)
	// ruleid: go.dir-mode-too-permissive
	os.Mkdir("tmp", 0o777)
}
