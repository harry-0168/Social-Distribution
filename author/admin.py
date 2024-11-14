from django.contrib import admin
from .models import Author, Following

class AuthorAdmin(admin.ModelAdmin):
    #Displays HOST, isNode and isTrusted Node. Also allow filtering
    list_display = ('displayName', 'host', 'isNode', 'isSharedNode')
    list_filter = ('isNode', 'isSharedNode') 
    search_fields = ('displayName', 'host')
    
    
# Register models 
admin.site.register(Author, AuthorAdmin)

admin.site.register(Following)