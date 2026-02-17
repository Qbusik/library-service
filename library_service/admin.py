from django.contrib import admin

from library_service.models import Borrowing, Book, Payment

admin.site.register(Book)
admin.site.register(Borrowing)
admin.site.register(Payment)
