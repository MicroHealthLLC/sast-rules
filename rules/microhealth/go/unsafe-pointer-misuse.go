package main

import (
	"syscall"
	"unsafe"

	"golang.org/x/sys/windows"
)

var proc = windows.NewLazySystemDLL("netapi32.dll").NewProc("NetUserGetInfo")

type info struct{ a, b uint32 }

func calls(name *uint16, buf *byte, n uint32) {
	var out *info
	// ok: go.unsafe-pointer-misuse
	proc.Call(0, uintptr(unsafe.Pointer(name)), 1, uintptr(unsafe.Pointer(&out)))
	// ok: go.unsafe-pointer-misuse
	syscall.Syscall(0, 2, uintptr(unsafe.Pointer(buf)), uintptr(n), 0)
	// ok: go.unsafe-pointer-misuse
	_ = uint32(unsafe.Sizeof(*out))
	// ok: go.unsafe-pointer-misuse
	_ = unsafe.Offsetof(out.b)

	// The address is computed in a uintptr before the call: invalid.
	// ruleid: go.unsafe-pointer-misuse
	proc.Call(0, uintptr(unsafe.Pointer(buf))+8)
	// A nested unsafe.Add inside an exempt argument is still reported.
	// ruleid: go.unsafe-pointer-misuse
	proc.Call(0, uintptr(unsafe.Pointer(unsafe.Add(unsafe.Pointer(buf), 8))))
	// A pointer kept as uintptr outside the call's argument list.
	// ruleid: go.unsafe-pointer-misuse
	p := uintptr(unsafe.Pointer(buf))
	proc.Call(0, p)
	// ruleid: go.unsafe-pointer-misuse
	_ = unsafe.Slice(buf, n)
	// ruleid: go.unsafe-pointer-misuse
	_ = (*info)(unsafe.Pointer(buf))
	// ruleid: go.unsafe-pointer-misuse
	_ = unsafe.String(buf, n)
}
