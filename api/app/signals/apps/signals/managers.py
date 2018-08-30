from django.db import models, transaction


class SignalManager(models.Manager):

    def create_initial(self, signal_data, location_data, status_data, category_data, reporter_data):
        with transaction.atomic():
            signal = self.create(signal_data)
            location = Location.objects.create(location_data)
            # ...

            signal.location = location
            # ...

            signal.save()

        # TODO trigger custom Django signal for initial create?

    def update_location(self, data):
        pass

    def update_status(self, data):
        pass

    def update_category(self, data):
        pass

    def update_reporter(self, data):
        pass
