from django.contrib import admin
from HITRAN.hitranmeta.models import Ref, OutputField, OutputCollection,\
                                     Source, NucSpins

class RefAdmin(admin.ModelAdmin):
    ordering = ['id','refID']
    pass
admin.site.register(Ref, RefAdmin)

class OutputFieldAdmin(admin.ModelAdmin):
    pass
admin.site.register(OutputField, OutputFieldAdmin)

class OutputCollectionAdmin(admin.ModelAdmin):
    pass
admin.site.register(OutputCollection, OutputCollectionAdmin)

##################

class SourceAdmin(admin.ModelAdmin):
    list_display = ('id', '__unicode__')
    ordering = ['id',]
    pass
admin.site.register(Source, SourceAdmin)

class NucSpinsAdmin(admin.ModelAdmin):
    pass
admin.site.register(NucSpins, NucSpinsAdmin)
    


