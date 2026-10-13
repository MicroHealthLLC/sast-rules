import * as cp from 'child_process';

export function build(branch: string) {
  // ruleid: javascript.child-process-shell-command
  cp.exec(`git checkout ${branch}`);
}

export function runLine(line: string) {
  // ruleid: javascript.child-process-shell-command
  return cp.spawn(line, [], { shell: true });
}

export function runArgs(file: string, args: string[]) {
  // ruleid: javascript.child-process-shell-command
  return cp.execFileSync(file, args, { shell: process.platform === 'win32' });
}

export function safe(file: string, args: string[]) {
  // ok: javascript.child-process-shell-command
  return cp.spawn(file, args, { shell: false, windowsHide: true });
}

export function noShell(file: string, args: string[]) {
  // ok: javascript.child-process-shell-command
  return cp.execFile(file, args, { cwd: '/tmp' });
}

export function constant() {
  // ok: javascript.child-process-shell-command
  cp.exec('git --version');
}
