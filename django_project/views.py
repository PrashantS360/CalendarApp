import os
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from django.shortcuts import redirect
from django.views import View
from django.http import JsonResponse
from django.shortcuts import render

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
REDIRECT_URI = 'http://localhost:8000/rest/v1/calendar/redirect/'


def home(request):
    return render(request, 'index.html')


os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'


class GoogleCalendarInitView(View):

    def get(self, request):
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json',
            scopes=SCOPES
        )

        flow.redirect_uri = REDIRECT_URI

        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        request.session['state'] = state
        return redirect(authorization_url)


class GoogleCalendarRedirectView(View):

    def get(self, request):
        state = request.GET.get('state')

        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json',
            scopes=SCOPES,
            state=state
        )
        flow.redirect_uri = REDIRECT_URI

        authorization_response = request.build_absolute_uri()
        flow.fetch_token(authorization_response=authorization_response)

        credentials = flow.credentials

        request.session['credentials'] = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }

        return redirect('/rest/v1/calendar/events')


class GoogleCalendarEventsView(View):

    def get(self, request):
        credentials = Credentials(
            **request.session['credentials']
        )

        try:
            service = build('calendar', 'v3', credentials=credentials)

            # Call the Calendar API
            print('Getting the upcoming 10 events')
            events_result = service.events().list(calendarId='primary',
                                                  maxResults=10, singleEvents=True,
                                                  orderBy='startTime').execute()
            events = events_result.get('items', [])

            if not events:
                print('No upcoming events found.')
                return JsonResponse({"status": "fail"})

        except Exception as error:
            print('An error occurred: %s' % error)

        return render(request, 'calendar.html', {'events': events})
