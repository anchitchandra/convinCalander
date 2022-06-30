import json
import datetime
import os
from rest_framework.response import Response
from rest_framework.views import APIView

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']



class GoogleCalendarInitView(APIView):

    def post(self, request):
        try:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", scopes=SCOPES)
                
            creds = flow.run_local_server(port=8080)
            request.session['creds'] = creds.to_json()
            print(creds.to_json())
            return Response(data={"status": True}, status=200)
        except:
            return Response(data={"status": False}, status=400)


class GoogleCalendarRedirectView(APIView):
    def post(self, request):
        creds = None
        try:
            if os.path.exists('credentials.json'):
                creds = Credentials.from_authorized_user_info(json.loads(request.session.get('creds')), SCOPES)

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    return Response(data={"status": False, "msg": "Please Login Again"}, status=401)

            service = build('calendar', 'v3', credentials = creds)

            now = datetime.datetime.utcnow().isoformat() + 'Z'
            events_result = service.events().list(calendarId='primary', timeMin=now,
                                                maxResults=10, singleEvents=True,
                                                orderBy='startTime').execute()
            events = events_result.get('items', [])

            if not events:
                return Response(data={"status":True,'message':'No events found!'}, status=200)

            all_events = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                all_events.append({start : event['summary']})
            return Response(data={"status": True, "events": all_events}, status=200)

        except HttpError as h:
            return Response(data={"status": False, "msg": f"{h}"}, status=4002)
        