from rest_framework import serializers


class TripInputSerializer(serializers.Serializer):
	current_location = serializers.CharField()
	pickup_location = serializers.CharField()
	dropoff_location = serializers.CharField()
	current_cycle_used_hours = serializers.FloatField(min_value=0)



class StopSerializer(serializers.Serializer):
	type = serializers.ChoiceField(choices=['rest', 'fuel', 'pickup', 'dropoff'])
	name = serializers.CharField()
	lat = serializers.FloatField()
	lng = serializers.FloatField()
	duration_minutes = serializers.IntegerField()



class DayLogBlockSerializer(serializers.Serializer):
	status = serializers.ChoiceField(choices=['off_duty', 'sleeper', 'driving', 'on_duty'])
	start = serializers.CharField() # HH:MM in terminal timezone
	end = serializers.CharField()



class StepInstructionSerializer(serializers.Serializer):
	# Define fields for step instructions as needed
	instruction = serializers.CharField()
	distance = serializers.FloatField()
	duration = serializers.IntegerField()

class TripPlanSerializer(serializers.Serializer):
	distance_miles = serializers.FloatField()
	duration_minutes = serializers.IntegerField()
	polyline = serializers.CharField() # encoded route for map display
	stops = StopSerializer(many=True)
	logs = serializers.ListField(child=DayLogBlockSerializer(many=True))
	instructions = StepInstructionSerializer(many=True)
	polylines = serializers.ListField(child=serializers.CharField()) # list of encoded segments (for e.g. fuel stops)