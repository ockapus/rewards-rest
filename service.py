import json
import web
import datetime

urls = (
    # Return point balance for a specific user
    '/rest/users/(.*)', 'user',
    # Add or remove points
    '/rest/points/(.*)', 'points'
)

# Initialize with a single user, with empty points log
users = {
    "1": []
}

def get_totals(user):
    """Assuming previously validated user ID, return current point totals for all payers for that user
    """

success = { 'success': True }

app = web.application(urls, globals())

class points:
    def POST(self, user):
        """Add points to a given user

        Parameters:
        user (string): ID of user we want to spend points for

        Returns:
        Success

        """
        if user not in users:
            raise web.NotFound(message='User not found')

        # Validate our payload before attempting to process
        post_data = json.loads(web.data())
        if 'payer' not in post_data:
            raise web.BadRequest(message="Required field 'payer' not found in request body.")
        if not isinstance(post_data['payer'], str):
            raise web.BadRequest(message="Field 'payer' must be string.")
        if 'points' not in post_data:
            raise web.BadRequest(message="Required field 'points' not found in request body.")
        if not isinstance(post_data['points'], int):
            raise web.BadRequest(message="Field 'points' must be an integer.")
        if 'timestamp' not in post_data:
            raise web.BadRequest(message="Required field 'timestamp' not found in request body.")
        try:
            ourdate = datetime.datetime.fromisoformat(post_data['timestamp'])
        except:
            raise web.BadRequest(message="Field 'timestamp' must be valid iso datetime.")
        if ourdate > datetime.datetime.now():
            raise web.BadRequest(message="Field 'timestamp' cannot be in the future.")

        return json.dumps(success)


    def PUT(self, user):
        """Spend points on a given user

        Parameters:
        user (string): ID of user we want to spend points for

        Returns:
        JSON string of points deducted from specific payers
        """
        pass

class user:
    def GET(self, user):
        """Return information on a given user's points

        Parameters:
        user (string): ID of user we want information about

        Returns:
        JSON string of current points balance for the requested user

        """
        if user not in users:
            return web.NotFound(message='User not found')

        totals = {}
        # Go through list of log entries for this user; assume these are in date order
        for entry in users[user]:
            if entry[0] not in totals:
                totals[entry[0]] = 0
            totals[entry[0]] += totals[entry[2]]
        # Now return this as JSON
        points = { 'points': totals }
        return json.dumps(points)

if __name__ == "__main__":
    app.run()