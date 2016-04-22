# -*- coding: utf-8 -*-

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
#from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from ..models.students import Student
from ..models.groups import Group
from endless_pagination.decorators import page_template
from endless_pagination import utils
from datetime import datetime
from django.core.urlresolvers import reverse

from django.forms import ModelForm
from django.views.generic import ListView, UpdateView, DeleteView

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from crispy_forms.bootstrap import FormActions


@page_template('students/students_page.html')
def students_list(request,
                  template='students/students_list.html',
                  page_template='students/students_page.html',
                  extra_context=None):
    students = Student.objects.all().order_by('last_name')

    order_by = request.GET.get('order_by', '')
    if order_by in ('last_name', 'first_name', 'card', 'id'):
        students = students.order_by(order_by)
        if request.GET.get('reverse', '') == '1':
            students = students.reverse()

    context = {'students': students,
               'page_template': page_template,
               'start_id': (utils.get_page_number_from_request(request) - 1) * 3,
               'per_page': 10}

    if extra_context is not None:
        context.update(extra_context)
    if request.is_ajax():
        template = page_template

    return render(request, template, context)


def students_add(request):
    if request.method == "POST":
        if request.POST.get('add_button') is not None:
            errors = {}

            data = {'middle_name': request.POST.get('middle_name'),
                    'notes': request.POST.get('notes')}

            # validating user input
            first_name = request.POST.get('first_name', '').strip()
            if not first_name:
                errors['first_name'] = u"Імʼя є обовʼязковим"
            else:
                data['first_name'] = first_name

            last_name = request.POST.get('last_name', '').strip()
            if not last_name:
                errors['last_name'] = u"Прізвище є обовʼязковим"
            else:
                data['last_name'] = last_name

            birth_date = request.POST.get('birth_date', '').strip()
            if not birth_date:
                errors['birth_date'] = u"Дата народження є обовʼязковою"
            else:
                try:
                    datetime.strptime(birth_date, '%Y-%m-%d')
                except Exception:
                    errors[
                        'birth_date'] = u"Введіть коректний формат дати (напр. 1987-12-30)"
                else:
                    data['birth_date'] = birth_date

            card = request.POST.get('card', '').strip()
            if not card:
                errors['card'] = u"Номер білета є обовʼязковим"
            else:
                data['card'] = card

            student_group = request.POST.get('student_group', '').strip()
            if not student_group:
                errors['student_group'] = u"Група є обовʼязковою"
            else:
                groups = Group.objects.filter(pk=student_group)
                if len(groups) != 1:
                    errors['student_group'] = u"Оберіть коректну групу"
                else:
                    data['student_group'] = groups[0]

            photo = request.FILES.get('photo')
            if photo:
                data['photo'] = photo

            if not errors:
                student = Student(**data)
                student.save()
                return HttpResponseRedirect(u'%s?status_message=Студента успішно додано!' % reverse('home'))
            else:
                return render(request, 'students/students_add.html',
                              {'groups': Group.objects.all().order_by('title'),
                               'errors': errors})
        elif request.POST.get('cancel_button') is not None:
            return HttpResponseRedirect(u'%s?status_message=Додавання студента скасовано!' % reverse('home'))
    else:
        return render(request, 'students/students_add.html',
                      {'groups': Group.objects.all().order_by('title')})


def students_delete(request, sid):
    return HttpResponse('<h1>Delete student %s</h1>' % sid)


class StudentList(ListView):
    model = Student
    context_object_name = 'students'
    template = 'students/student_class_based_view_template'

    def get_context_data(self, **kwargs):
        """ This method adds extra variables to template"""
        # get original context data from parent class
        context = super(StudentList, self).get_context_data(**kwargs)

        # tell template not to show logo on a page
        context['show_logo'] = False

        # return context mapping
        return context

    def get_queryset(self):
        """ Order students by last_name"""
        # get original query set
        qs = super(StudentList, self).get_queryset()

        # order by last name
        return qs.order_by('last_name')


class StudentUpdateForm(ModelForm):

    class Meta:
        model = Student
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(StudentUpdateForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)

        # set form tag attributes
        self.helper.form_action = reverse(
            'students_edit', kwargs={'pk': kwargs['instance'].id})
        self.helper.form_method = 'POST'
        self.helper.form_class = 'form-horizontal'

        # set form field properties
        self.helper.help_text_inline = True
        self.helper.html5_required = True
        self.helper.label_class = 'col-sm-2 control-label'
        self.helper.field_class = 'col-sm-10'

        # add buttons
        self.helper.layout[-1] = FormActions(
            Submit('add_button', u'Зберегти', css_class="btn btn-primary"),
            Submit('cancel_button', u'Скасувати', css_class="btn btn-link"),
        )


class StudentUpdateView(UpdateView):
    model = Student
    template_name = 'students/students_edit.html'
    form_class = StudentUpdateForm

    def get_success_url(self):
        return u"%s?status_message=Студента успішно збережено!" % reverse('home')

    def post(self, request, *args, **kwargs):
        if request.POST.get('cancel_button'):
            return HttpResponseRedirect(u'%s?status_message=Редагування студента відмінено!' % reverse('home'))
        else:
            return super(StudentUpdateView, self).post(request, *args, **kwargs)


class StudentDeleteView(DeleteView):
    model = Student
    template_name = 'students/students_confirm_delete.html'

    def get_success_url(self):
        return u"%s?status_message=Студента успішно видалено!" % reverse('home')
