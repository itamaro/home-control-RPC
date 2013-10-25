from django.contrib import admin
import rhost

admin.site.register(rhost.models.RemoteHost)
admin.site.register(rhost.models.SshHost)
admin.site.register(rhost.models.EsxiHost)
