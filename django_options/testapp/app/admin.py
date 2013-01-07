from django import forms
from django.contrib.admin.widgets import AdminFileWidget

from django_options.admin import OptionsPage, admin_pages, option
from django_options.forms import OptionsForm

class GeneralsAdminPage(OptionsPage):

    title = "General options"
    description = "Very important options"
    code = 'generals'


    class SiteInfoForm(OptionsForm):

        code = 'site_info'
        title = 'Site information'
        description = 'small info'

        # options
        site_title = option(forms.CharField(max_length=255))
        site_description = option(forms.CharField(widget=forms.Textarea))

#    form_class = SiteInfoForm # auto discovered


    class SubGeneralsAdminPage(OptionsPage):

        title = "Site aspect"
        description = "Something related to global options"
        code = "subgenerals"
#        parent = GeneralsAdminPage # auto discovered

        class SiteSubInfoForm(OptionsForm):

            code = 'site_sub_info'
            title = ''

            # options
            site_keywords = option(forms.CharField(widget=forms.Textarea))
            site_theme = option(forms.ChoiceField(choices=(
                ('', '-- Empty --'),
                ('basic', 'Basic theme'),
                ('advanced', 'Advanced theme'),
                )))

    #    form_class = SiteSubInfoForm # auto discovered


    class SubSubGeneralsAdminPage(OptionsPage):

        title = "Site profile"
        description = "#2 Something related to global options"
        code = "subgenerals2"
#        parent = GeneralsAdminPage # auto discovered

        class SiteSubInfoForm(OptionsForm):

            code = 'site_sub_info2'
            description = 'Sub site info'
            options = (('site_author','site_author_email'),)

            # options
            site_author = option(forms.CharField(max_length=100))
            site_author_email = option(forms.EmailField())

        class ProfileInfoForm(OptionsForm):

            code = 'user_profile'
            title = ''
            optionsets = (('User profile', {'fields': ('avatar',('password','password_confirm',),)}),)

            # options
            avatar = option(forms.FileField(widget=AdminFileWidget, required=False, initial=True))
            password = option(forms.CharField(max_length=255, widget= forms.PasswordInput, required=False))
            password_confirm = forms.CharField(max_length=255, widget= forms.PasswordInput, required=False)


            def clean(self):
                passphrase = self.cleaned_data.get('password')

                if passphrase:
                    passphrase_confirm = self.cleaned_data.get('password_confirm')
                    if passphrase != passphrase_confirm:
                        raise forms.ValidationError("Passwords not matches")

                return self.cleaned_data

        class ProfileLoginForm(OptionsForm):

            code = 'user_profile_login'

            password_check = forms.CharField(max_length=255, widget= forms.PasswordInput)

            def clean_password_check(self):
                from django_options import get_option
                if self.cleaned_data.get('password_check') != get_option('password'):
                    raise forms.ValidationError('Invalid password')
                return self.cleaned_data.get('password_check')

        # to choose order of forms
        form_class_list = [SiteSubInfoForm, ProfileInfoForm, ProfileLoginForm]

class OtherAdminPage(OptionsPage):

    title = "Other options"
    description = "some options"
    code = 'others'

    class SiteInfoForm(OptionsForm):

        code = 'other_info'
        title = 'Other information'

        # options
        my_stuff = option(forms.CharField(max_length=255), option_key='my.stuff')
        some_stuff = option(forms.CharField(max_length=255))
        other_stuff = option(forms.CharField(widget=forms.Textarea, required=False))

        optionsets = (
            (None, {
                'fields': (('my_stuff','some_stuff',),)
            }),
            ('Advanced options', {
                'classes': ('collapse',),
                'fields': ('other_stuff',)
            }),
        )
#    form_class = SiteInfoForm # auto discovered

    class CustomPage(OptionsPage):

        title = "Custom page"
        code = "custom_page"
        template_name = 'admin/custom_page.html'




admin_pages.register(GeneralsAdminPage)
#option_pages.register(SubGeneralsAdminPage) # auto discovered
#option_pages.register(SubSubGeneralsAdminPage) # auto discovered

admin_pages.register(OtherAdminPage)