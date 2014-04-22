from django.shortcuts import render_to_response


def home(request):
    """Dashboard for Agile Project Management tool"""
    #return HttpResponse('Looking for template in miner/explorer.html')
    return render_to_response('agile/home.html')
