from django.contrib import admin

from home.models import Owner, SuperAdmin, Organizer, Talent, Partner, Team, Gest

admin.site.register(Owner)
admin.site.register(SuperAdmin)
admin.site.register(Organizer)
admin.site.register(Talent)
admin.site.register(Partner)
admin.site.register(Team)
admin.site.register(Gest)