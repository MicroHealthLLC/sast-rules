package main

import (
	"archive/tar"
	"bytes"
	"compress/gzip"
	"io"
	"os"
)

func unpack(data []byte, f *os.File) {
	gz, _ := gzip.NewReader(bytes.NewReader(data))
	tr := tar.NewReader(gz)
	// ruleid: go.decompression-without-limit
	io.Copy(f, tr)
	// ruleid: go.decompression-without-limit
	io.ReadAll(gz)
	// ok: go.decompression-without-limit
	io.Copy(f, io.LimitReader(tr, 1<<20))
	lr := io.LimitReader(gz, 1<<20)
	// ok: go.decompression-without-limit
	io.ReadAll(lr)
}
