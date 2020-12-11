import os
from datetime import datetime
import re
import logging
from ftplib import FTP
from ftplib import error_perm
_logger = logging.getLogger(__name__)
try:
    import pysftp
except ImportError:
    _logger.warn('This module needs pysftp to automaticly write backups to the FTP through SFTP. Please install pysftp on your system. (sudo pip install pysftp)')

from odoo import models, api, fields
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError
from odoo import tools


class FtpConfig(models.Model):
    
    _name = 'ftp.config'
    _description = 'Configuracion FTP'
    _rec_name = 'sftp_ip' 
    
    TIMEOUT = 5
    
    files_path = fields.Char('Ruta local csv')
    sftp_path = fields.Char('Ruta servidor csv')
    sftp_ip = fields.Char('Servidor')
    sftp_username = fields.Char('Usuario')
    sftp_password = fields.Char('Password')
    sftp_port = fields.Integer('Puerto')
    sftp_autoremove = fields.Boolean('Eliminar archivos automaticamente?')
    sftp_days_unlink = fields.Integer('Eliminar archivos despues de')
    send_mail_sftp_fail = fields.Boolean('Enviar correo?')
    email_to_notify = fields.Char('E-mail')
    local_autoremove = fields.Boolean('Eliminar archivos automaticamente?')
    local_days_unlink = fields.Integer('Eliminar archivos despues de')
    protocol_use = fields.Selection([
        ('ftp','FPT'),
        ('sftp','SFTP'),
    ], string='Protocolo a usar')
    
    @api.onchange('protocol_use',)
    def _onchange_protocol_use(self):
        if self.protocol_use == 'ftp':
            self.sftp_port = 21
        elif self.protocol_use == 'sftp':
            self.sftp_port = 22

    @api.multi
    def test_sftp_connection(self):
        self.ensure_one()
        messageContent = ""
        try:
            ipHost = self.sftp_ip
            usernameLogin = self.sftp_username
            passwordLogin = self.sftp_password
            port = self.sftp_port
            #Connect with external server over SFTP, so we know sure that everything works.
            if self.protocol_use == 'sftp':
                srv = pysftp.Connection(host=ipHost, username=usernameLogin, password=passwordLogin, port=port)
                srv.close()
            else:
                srv = FTP()
                srv.connect(host=ipHost, port=port, timeout=self.TIMEOUT)
                srv.login(user=usernameLogin, passwd=passwordLogin)
                srv.close()
            #We have a success.
            messageContent = "Conexión exitosa!\n"
            messageContent += "Todo parece estar correctamente configurado!"
        except Exception as e:
            messageContent = "Conexión Fallida!\n"
            if len(self.sftp_ip) < 8:
                messageContent += "Tu Dirección IP es muy corta.\n"
            messageContent += "Esto es lo que se obtuvo:\n"
            messageContent += tools.ustr(e)
        raise UserError(messageContent)

    @api.multi
    def unlink_local_files(self):
        #eliminar archivos locales
        if self.local_autoremove and self.local_days_unlink > 0 :
            files_path = self.files_path
            #Loop over all files in the directory.
            for f in os.listdir(files_path):
                fullpath = os.path.join(files_path, f)
                timestamp = os.stat(fullpath).st_ctime
                createtime = datetime.fromtimestamp(timestamp)
                now = datetime.now()
                delta  = now - createtime
                if delta.days >= self.local_days_unlink:
                    #Only delete files (which are .dump), no directories.
                    if os.path.isfile(fullpath) and ".csv" in f:
                        _logger.info("Delete: " + fullpath)
                        os.remove(fullpath)
                        
    @api.multi
    def ensure_local_path(self):
        if not os.path.exists(self.files_path):
            try:
                os.mkdir(self.files_path)
            except OSError:
                raise UserError("No tiene permisos en la ruta %s, por favor verifique" % self.files_path)
            except IOError:
                raise UserError("No tiene permisos en la ruta %s, por favor verifique" % self.files_path)
    
    @api.multi
    def _send_by_sftp(self, fullpath, file_name):
        #Store all values in variables
        pathToWriteTo = self.sftp_path
        ipHost = self.sftp_ip
        usernameLogin = self.sftp_username
        passwordLogin = self.sftp_password
        port = self.sftp_port
        self.ensure_local_path()
        sent_ok = True
        try:
            #Connect with external server over SFTP
            srv = pysftp.Connection(host=ipHost, username=usernameLogin, password=passwordLogin, port=port)
            #set keepalive to prevent socket closed / connection dropped error
            srv._transport.set_keepalive(30)
            #Move to the correct directory on external server. If the user made a typo in his path with multiple slashes (/odoo//backups/) it will be fixed by this regex.
            pathToWriteTo = re.sub('([/]{2,5})+','/',pathToWriteTo)
            _logger.info(pathToWriteTo)
            try:
                srv.chdir(pathToWriteTo)
            except IOError:
                #Create directory and subdirs if they do not exist.
                currentDir = ''
                for dirElement in pathToWriteTo.split('/'):
                    currentDir += dirElement + '/'
                    try:
                        srv.chdir(currentDir)
                    except:
                        _logger.info('(Part of the) path didn\'t exist. Creating it now at ' + currentDir)
                        #Make directory and then navigate into it
                        srv.mkdir(currentDir, mode=777)
                        srv.chdir(currentDir)
                        pass
            srv.chdir(pathToWriteTo)
            #Loop over all files in the directory.
            if os.path.isfile(fullpath):
                _logger.info("Send file %s" % fullpath)
                srv.put(fullpath)
            #Navigate in to the correct folder.
            srv.chdir(pathToWriteTo)
            #Loop over all files in the directory from the back-ups.
            #We will check the creation date of every back-up.
            if self.sftp_autoremove and self.sftp_days_unlink > 0:
                for file_name in srv.listdir(pathToWriteTo):
                    #Get the full path
                    fullpath = os.path.join(pathToWriteTo, file_name) 
                    #Get the timestamp from the file on the external server
                    timestamp = srv.stat(fullpath).st_atime
                    createtime = datetime.fromtimestamp(timestamp)
                    now = datetime.now()
                    delta = now - createtime
                    #If the file is older than the daystokeepsftp (the days to keep that the user filled in on the Odoo form it will be removed.
                    if delta.days >= self.sftp_days_unlink:
                        #Only delete files, no directories!
                        if srv.isfile(fullpath) and ".csv" in file_name:
                            _logger.info("Delete: " + file_name)
                            srv.unlink(file_name)
            #Close the SFTP session.
            srv.close()
        except Exception as e:
            sent_ok = False
            _logger.info('Error! no se puede enviar archivo al servidor')
            #enviar mail de error
            if self.send_mail_sftp_fail:
                try:
                    ir_mail_server = self.env['ir.mail_server']
                    email_from = "soporte_odoo@laotraopcion.cl"
                    message = "Estimado,\n\n El envío del archivo %s al servidor: %s Falló, "\
                                "por favor verifique los parametros de conexión. \n\n Detalles del error: %s" % \
                                (fullpath, self.sftp_ip, tools.ustr(e))
                    msg = ir_mail_server.build_email(email_from, [self.email_to_notify], "Envio de Ventas en csv Fallido", message) 
                    ir_mail_server.send_email(msg)
                except Exception:
                    pass
        self.unlink_local_files()
        return sent_ok

    @api.multi
    def _send_by_ftp(self, fullpath, file_name):
        #Store all values in variables
        pathToWriteTo = self.sftp_path
        ipHost = self.sftp_ip
        usernameLogin = self.sftp_username
        passwordLogin = self.sftp_password
        port = self.sftp_port
        self.ensure_local_path()
        sent_ok = True
        try:
            #Connect with external server over FTP
            srv = FTP()
            srv.connect(host=ipHost, port=port, timeout=self.TIMEOUT)
            srv.login(user=usernameLogin, passwd=passwordLogin)
            #Move to the correct directory on external server. If the user made a typo in his path with multiple slashes (/odoo//backups/) it will be fixed by this regex.
            pathToWriteTo = re.sub('([/]{2,5})+','/',pathToWriteTo)
            _logger.info(pathToWriteTo)
            try:
                srv.cwd(pathToWriteTo)
            except error_perm:
                #Create directory and subdirs if they do not exist.
                currentDir = ''
                for dirElement in pathToWriteTo.split('/'):
                    currentDir += dirElement + '/'
                    try:
                        srv.cwd(currentDir)
                    except:
                        _logger.info('(Part of the) path didn\'t exist. Creating it now at ' + currentDir)
                        #Make directory and then navigate into it
                        srv.mkd(currentDir)
                        srv.cwd(currentDir)
                        pass
            srv.cwd(pathToWriteTo)
            #Loop over all files in the directory.
            if os.path.isfile(fullpath):
                _logger.info("Send file %s" % fullpath)
                file_send = open(fullpath, 'rb')
                srv.storbinary("STOR %s" % file_name, file_send)
                file_send.close()
            #Navigate in to the correct folder.
            srv.cwd(pathToWriteTo)
            #Loop over all files in the directory from the back-ups.
            #We will check the creation date of every back-up.
            if self.sftp_autoremove and self.sftp_days_unlink > 0:
                for file_name in srv.nlst():
                    #Get the full path
                    fullpath = os.path.join(pathToWriteTo, file_name) 
                    #Get the timestamp from the file on the external server
                    modifiedTime = srv.sendcmd('MDTM ' + file_name)
                    createtime = datetime.strptime(modifiedTime[4:], "%Y%m%d%H%M%S")
                    now = datetime.now()
                    delta = now - createtime
                    #If the file is older than the daystokeepsftp (the days to keep that the user filled in on the Odoo form it will be removed.
                    if delta.days >= self.sftp_days_unlink:
                        #Only delete files, no directories!
                        if srv.size(fullpath) is not None and ".csv" in file_name:
                            _logger.info("Delete: " + file_name)
                            srv.delete(file_name)
            #Close the SFTP session.
            srv.close()
        except Exception as e:
            sent_ok = False
            _logger.info('Error! no se puede enviar archivo al servidor: %s' % tools.ustr(e))
            #enviar mail de error
            if self.send_mail_sftp_fail:
                try:
                    ir_mail_server = self.env['ir.mail_server']
                    email_from = "soporte_odoo@laotraopcion.cl"
                    message = "Estimado,\n\n El envío del archivo %s al servidor: %s Falló, "\
                                "por favor verifique los parametros de conexión. \n\n Detalles del error: %s" % \
                                (fullpath, self.sftp_ip, tools.ustr(e))
                    msg = ir_mail_server.build_email(email_from, [self.email_to_notify], "Envio de Ventas en csv Fallido", message) 
                    ir_mail_server.send_email(msg)
                except Exception:
                    pass
        self.unlink_local_files()
        return sent_ok
