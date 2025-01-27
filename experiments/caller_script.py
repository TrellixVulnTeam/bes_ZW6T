#!/usr/bin/env python3
import argparse
import os
import os.path as path
import platform
import socket
import subprocess
import sys
import sys
import tarfile
import tempfile
import zipfile

class package_caller(object):

  def __init__(self):
    pass
  
  def main(self):
    p = argparse.ArgumentParser()
    p.add_argument('-v', '--verbose', action = 'store_true', default = False,
                   help = 'Verbose log output [ False ]')
    p.add_argument('--debug', action = 'store_true', default = False,
                   help = 'Debug mode.  Save temp files and log the script itself [ False ]')
    p.add_argument('--tty', action = 'store', default = None,
                   help = 'tty to log to in debug mode [ False ]')
    p.add_argument('--tail-log-port', action = 'store', default = None, type = int,
                   help = 'port to send to for tailing [ False ]')
    p.add_argument('package_zip', action = 'store', default = None,
                   help = 'The package []')
    p.add_argument('entry_command', action = 'store', default = None,
                   help = 'The entry command []')
    p.add_argument('output_log', action = 'store', default = None,
                   help = 'The output log file []')
    p.add_argument('entry_command_args', action = 'store', default = [], nargs = '*',
                   help = 'Optional entry command args [ ]')
    args = p.parse_args()
    # make sure the log exists so even if the command fails theres something
    with open(args.output_log, 'w') as fout:
      fout.write('')
      fout.flush()
    self._debug = args.debug
    self._name = path.basename(sys.argv[0])
    self._console_device = args.tty or self._find_console_device()
    self._socket = None
    for key, value in sorted(args.__dict__.items()):
      self._log('args: {}={}'.format(key, value))
    tmp_dir = path.join(path.dirname(args.package_zip), 'work')
    self._log('tmp_dir={}'.format(tmp_dir))

    self._log('package_zip={} entry_command={} output_log={}'.format(args.package_zip,
                                                                     args.entry_command,
                                                                     args.output_log))

    self._unpack_package(args.package_zip, tmp_dir)
    self._start_socket(args.tail_log_port)
    exit_code = self._execute(tmp_dir,
                              args.entry_command,
                              args.output_log,
                              args.entry_command_args)
    self._stop_socket()
    return exit_code

  def _start_socket(self, port):
    if not port:
      return
    address = ( 'localhost', port )
    self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self._log('binding socket to port {}'.format(port))
    self._socket.bind(address)

  def _stop_socket(self):
    if self._socket:
      self._socket.close()
    self._socket = None
    
  def _execute(self, dest_dir, command, output_log, entry_command_args):
    entry_command_args = entry_command_args or []
    stdout_pipe = subprocess.PIPE
    stderr_pipe = subprocess.STDOUT
    command_abs = path.join(dest_dir, command)
    if not path.isfile(command_abs):
      raise IOError('entry command not found: "{}"'.format(command_abs))
    args = [ command_abs ] + entry_command_args
    self._log('args={} cwd={}'.format(args, dest_dir))
    os.chmod(command_abs, 0o0755)
    process = subprocess.Popen(args,
                               stdout = stdout_pipe,
                               stderr = stderr_pipe,
                               shell = False,
                               cwd = dest_dir,
                               universal_newlines = True)

    if self._socket:
      self._log('socket listening')
      self._socket.listen(1)
      self._log('calling accept')
      connection, client_address = self._socket.accept()
      self._log('connection={} client_address={}'.format(connection, client_address))

    stdout_lines = []
    if False:
      # Poll process for new output until finished
      while True:
        nextline = process.stdout.readline()
        if nextline == '' and process.poll() != None:
            break
        stdout_lines.append(nextline)
        self._log('process: {}'.format(nextline))

    output = process.communicate()
    exit_code = process.wait()
    self._mkdir(path.dirname(output_log))
    stdout = output[0]
    with open(output_log, 'a') as fout:
      fout.write(stdout)
      fout.flush()
    return exit_code

  @classmethod
  def _mkdir(clazz, p):
    if path.isdir(p):
      return
    os.makedirs(p)
  
  def _unpack_package_zip(self, package_zip, dest_dir):
    with zipfile.ZipFile(package_zip, mode = 'r') as f:
      f.extractall(path = dest_dir)

  def _unpack_package_tar(self, package_tar, dest_dir):
    with tarfile.open(package_tar, mode = 'r') as f:
      def is_within_directory(directory, target):
          
          abs_directory = os.path.abspath(directory)
          abs_target = os.path.abspath(target)
      
          prefix = os.path.commonprefix([abs_directory, abs_target])
          
          return prefix == abs_directory
      
      def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
      
          for member in tar.getmembers():
              member_path = os.path.join(path, member.name)
              if not is_within_directory(path, member_path):
                  raise Exception("Attempted Path Traversal in Tar File")
      
          tar.extractall(path, members, numeric_owner=numeric_owner) 
          
      
      safe_extract(f, path=dest_dir)

  def _unpack_package(self, package, dest_dir):
    if zipfile.is_zipfile(package):
      self._unpack_package_zip(package, dest_dir)
    elif tarfile.is_tarfile(package):
      self._unpack_package_tar(package, dest_dir)
    else:
      raise RuntimeError('unknown archive type: "{}"'.format(package))
      
  def _log(self, message):
    if not self._debug:
      return
    s = '{}: {}\n'.format(self._name, message)
    with open(self._console_device, 'w') as f:
      f.write(s)
      f.flush()

  @classmethod
  def _find_console_device(clazz):
    system = platform.system()
    if system == 'Windows':
      return 'con:'
    elif system == 'Darwin':
      return '/dev/ttys000'
    elif system == 'Linux':
      return '/dev/console'
    else:
      raise RuntimeError('unknown platform: "{}"'.format(system))

  @classmethod
  def run(clazz):
    raise SystemExit(package_caller().main())

if __name__ == '__main__':
  package_caller.run()
