from django.shortcuts import render
from rest_framework.generics import ListCreateAPIView, RetrieveAPIView

# Create your views here.


class LogListCreateView(ListCreateAPIView):
    pass


class LogRetrieveAPiView(RetrieveAPIView):
    pass
