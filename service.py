import json
import copy
import web
import datetime
from time import strftime

urls = (
    # Return point balance for a specific user
    '/rest/users/(.*)', 'user',
    # Add or remove points
    '/rest/points/(.*)', 'points'
)

# Initialize with a single user, with empty points log
# Entries in the array will be in format: [{payer}, {datetime}, {points}]
users = {
    "1": []
}

app = web.application(urls, globals())

class points:
    def POST(self, user):
        """Add points to a given user

        Parameters:
        user (string): ID of user we want to spend points for

        Request Body:
        JSON string expected in the form of:
            {
                'payer': string,
                'points': int,
                'timestamp': string in ISO datetime format
            }

        Returns:
        Success as JSON

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
            entrydate = datetime.datetime.fromisoformat(post_data['timestamp'])
        except:
            raise web.BadRequest(message="Field 'timestamp' must be valid iso datetime.")
        if entrydate > datetime.datetime.now():
            raise web.BadRequest(message="Field 'timestamp' cannot be in the future.")

        # If we're trying to add negative points, make sure we never end up with an amount
        # less than zero for the given payer in the past
        if post_data['points'] < 0:
            sorted_list = sorted(users[user], key = lambda x: x[1])
            running_totals = {}
            for index in range(0, len(sorted_list) + 1):
                # If we've gone through our whole log for this user, or the next log entry
                # is after the new entry we want to add, check our point totals
                if index == len(sorted_list) or sorted_list[index][1] > entrydate:
                    if (post_data['payer'] not in running_totals or 
                        running_totals[post_data['payer']] + post_data['points'] < 0):
                        raise web.BadRequest(
                            message='Negative point total at given datetime would result ' +
                            'in historical point total less than zero for specified payer.'
                        )
                else:
                    if sorted_list[index][0] not in running_totals:
                        running_totals[sorted_list[index][0]] = 0
                    running_totals[sorted_list[index][0]] += sorted_list[index][2]

        # If we've finished all validation, payload can be added to our log
        users[user].append([post_data['payer'], entrydate, post_data['points']])

        return json.dumps( { 'success': True } )


    def PUT(self, user):
        """Spend points on a given user

        Parameters:
        user (string): ID of user we want to spend points for

        Request Body:
        JSON string expected in the form of:
            {
                'points': int
            }

        Returns:
        JSON array of points deducted from specific payers, each item in form of:
            {
                'payer': string,
                'points': int,
                'timestamp': string in ISO datetime format
            }

        """
        if user not in users:
            raise web.NotFound(message='User not found')

        # Validate our payload before attempting to process
        post_data = json.loads(web.data())
        if 'points' not in post_data:
            raise web.BadRequest(message="Required field 'points' not found in request body.")
        if not isinstance(post_data['points'], int):
            raise web.BadRequest(message="Field 'points' must be an integer.")
        if post_data['points'] < 0:
            raise web.BadRequest(message="Field 'points' must be positive value.")

        # Now validate to make certain we're not going to end up with any negative points
        total = 0
        for entry in users[user]:
            total += entry[2]
        if post_data['points'] > total:
            raise web.BadRequest(message="Not enough total points for requested deduction.")

        # To figure out age of points, go through our log for this user and collapse previous spends.
        # Since we don't allow values to ever be negative, even when adding to the past, we can safely
        # assume processing previous spends will never give us a negative 'total' we have to worry about 
        # Note: grab deepcopy of the list so we can make updates without mangling original entries
        sorted_log = copy.deepcopy(sorted(users[user], key = lambda x: x[1]))
        to_purge = []
        for index in range(0, len(sorted_log)):
            if sorted_log[index][2] < 0:
                remaining_spend = abs(sorted_log[index][2])
                # If we find an entry we need to subtract, go back through all entries up until now
                for sub in range(0, index):
                    # If we find a positive value from same payer, subtract as many as we can
                    if sorted_log[index][0] == sorted_log[sub][0] and sorted_log[sub][2] > 0:
                        spend = min(remaining_spend, sorted_log[sub][2])
                        sorted_log[sub][2] -= spend
                        remaining_spend -= spend
                        # If we spent everything in this historical entry, track it to purge
                        if sorted_log[sub][2] == 0:
                            to_purge.append(sub)
                        # We're done if we've removed all these points
                        if remaining_spend == 0:
                            break
                # If we get here and still have something to spend, there's a problem in our data
                if remaining_spend > 0:
                    raise web.Conflict(message="Data problem resulted in error with point totals.")
                # Keep track of this entry to remove after we've gone through everything
                to_purge.append(index)
        # Now remove our extraneous log entries, to make it easier to do final deduction calculations
        to_purge.sort(reverse=True)
        for i in to_purge:
            del sorted_log[i]

        # Go through processed sorted log, and figure out how many points to remove from each payer        
        deductions = {}
        remaining_deduction = post_data['points']
        for l in sorted_log:
            if l[0] not in deductions:
                deductions[l[0]] = 0
            spend = min(remaining_deduction, l[2])
            deductions[l[0]] -= spend
            remaining_deduction -= spend
            if remaining_deduction == 0:
                break
        # If we get here and still have deductions to spend, there's a problem in our data
        if remaining_deduction > 0:
            raise web.Conflict(message="Data problem resulted in error with point totals.")

        # Otherwise: add these new deductions to our log, and report results
        results = []
        for payer, spend in deductions.items():
            users[user].append([payer, datetime.datetime.now(), spend])
            results.append({'payer': payer, 'points': spend, 'timestamp': strftime("%Y-%m-%d %H:%M:%S")})

        return json.dumps({'results': results})
        

class user:
    def GET(self, user):
        """Return information on a given user's points

        Parameters:
        user (string): ID of user we want information about

        Returns:
        JSON dictionary of points available, in key/value pairs of payer: remaining points

        """
        if user not in users:
            return web.NotFound(message='User not found')

        points = {}
        for entry in users[user]:
            if entry[0] not in points:
                points[entry[0]] = 0
            points[entry[0]] += entry[2]
        return json.dumps({ 'points': points })

if __name__ == "__main__":
    app.run()