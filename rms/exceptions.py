from django.utils.timezone import localtime


class ReservationError(ValueError):
    def __init__(self, message, collisions):
        super(ReservationError, self).__init__(message)
        self.collisions = collisions

    def get_json_dir(self):
        json_data = {
            'msg': str(self),
            'collisions': []
        }
        for reservation in self.collisions:
            json_data['collisions'].append({
                'id': reservation.id,
                'full_id': reservation.full_id,
                'name': reservation.name,
                'start': localtime(reservation.start_date).isoformat(),
                'end': localtime(reservation.end_date).isoformat()
            })
        return json_data


class CheckoutError(ReservationError):
    def __init__(self, *args, **kwargs):
        super(CheckoutError, self).__init__(*args, **kwargs)


class CheckinError(ValueError):
    def __init__(self, message):
        super(CheckinError, self).__init__(message)

