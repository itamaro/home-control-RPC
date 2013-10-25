import sys
import time
import subprocess
import re
import logging
from awake import wol
import paramiko

from django.db import models

logger = logging.getLogger(__name__)

WIN = LINUX = False
PINGS_FOR_CHECK = 3
MOCK_SSH = False
if 'win32' == sys.platform:
    WIN = True
    ping_cmd = ['ping', '-n', str(PINGS_FOR_CHECK)]
    ping_result_re = re.compile('Packets\: Sent \= (?P<sent>\d{1})\, '
                                'Received \= (?P<recv>\d{1})')
else:
    LINUX = True
    ping_cmd = ['ping', '-c', str(PINGS_FOR_CHECK)]
    ping_result_re = re.compile('\b(?P<sent>\d{1}) packets transmitted\, '
                                '(?P<recv>\d{1}) received\b')

vm_re = re.compile('(?P<vmid>\d+)\s+(?P<name>\S+)\s+(?P<vmfile>\[\S+\] \S+)'
                   '\s+(?P<guest_os>\w+)\s+(?P<version>\S+).*')
vm_powerstate_re = re.compile('Powered (?P<power>\w{2,3})$')

class RemoteHost(models.Model):
    name = models.CharField(max_length=100, unique=True)
    ip_address = models.IPAddressField(verbose_name='IP Address')
    mac_address = models.CharField(max_length=12+5, verbose_name='MAC Address')
    
    def __unicode__(self):
        return u'%s(%s, %s, %s)' % (self.__class__.__name__,
                                    self.name,
                                    self.ip_address,
                                    self.mac_address)
    
    def get_specialized_instance(self):
        try:
            return self.sshhost.get_specialized_instance()
        except self.DoesNotExist:
            return self
    
    def isHostUp(self):
        proc = subprocess.Popen(ping_cmd + [self.ip_address],
                                stdout=subprocess.PIPE)
        out, _ = proc.communicate()
        res = ping_result_re.search(out)
        return res and int(res.group('recv')) >= (1+PINGS_FOR_CHECK/2)  \
                or False
        
    def powerOn(self, max_wol_tries=3, pings_per_wol=5,
                wait_between_pings=30.0):
        for _ in xrange(max_wol_tries):
            wol.send_magic_packet(self.mac_address)
            time.sleep(5.0)
            for __ in xrange(pings_per_wol):
                if self.isHostUp():
                    return True
                time.sleep(wait_between_pings)
        return False
    
    def shutdown(self):
        # Not implemented for generic remote host
        return False

class SshHost(RemoteHost):
    ssh_port = models.PositiveIntegerField(verbose_name='SSH Port')
    root_user = models.CharField(max_length=100)
    root_pass = models.CharField(max_length=100)
    
    def get_specialized_instance(self):
        try:
            return self.esxihost.get_specialized_instance()
        except self.DoesNotExist:
            return self
    
    def runSshCommand(self, cmd):
        if MOCK_SSH:
            # TODO: Add mocking
            return 'Generic mocked response'
        # Open SSH Transport to SSH host
        t = paramiko.Transport((self.ip_address, self.ssh_port))
        t.start_client()
        t.auth_password(self.root_user, self.root_pass)
        # Open an SSH session and execute the command
        chan = t.open_session()
        chan.set_combine_stderr(True)
        chan.exec_command('%s ; echo exit_code=$?' % (cmd))
        stdout = ''
        x = chan.recv(1024)
        while x:
            stdout += x
            x = chan.recv(1024)
        chan.close()
        t.close()
        output = stdout.strip().split('\n')
        exit_code = re.match('exit_code\=(\-?\d+)', output[-1]).group(1)
        # TODO: do something with the exit code
        return '\n'.join(output[:-1])
    
    def shutdown(self):
        logger.debug('Shutting down as SSH host')
        # TODO: Run shutdown SSH command
        return True

class EsxiHost(SshHost):
    esxi_version = models.CharField(max_length=10)
    
    def get_specialized_instance(self):
        return self
    
    def shutdown(self):
        logger.debug('Shutting down as ESXi host')
        # TODO: Shutdown VMs (order?) (rely on ESXi?)
        # TODO: Run shutdown SSH command
        return True
    
    def listVirtualMachines(self):
        # Get lists of VM from ESXi host
        getallvms = self.runSshCommand('vim-cmd vmsvc/getallvms').strip()
        # Parse the list
        vm_list = [vm_match.groupdict()
                   for vm_match in vm_re.finditer(getallvms)]
        return vm_list
    
    def isVirtualMachineUp(self, vmid):
        # Get VM power state from ESXi host
        getpowerstate = self.runSshCommand('vim-cmd vmsvc/power.getstate %s' %
                                           (vmid)).strip()
        # Parse the response
        m = vm_powerstate_re.search(getpowerstate)
        if m:
            return m.groupdict()['power'] == 'on'
        raise RuntimeError('No VM "%s" on host "%s"' % (vmid, self.name))
    
    def turnOnVirtualMachine(self, vmid):
        return
        poweron = self.runSshCommand('vim-cmd vmsvc/power.on %s' %
                                     (vmid)).strip()
    
    def shutdownVirtualMachine(self, vmid):
        return
        shutdown = self.runSshCommand('vim-cmd vmsvc/power.shutdown %s' %
                                      (vmid)).strip()
