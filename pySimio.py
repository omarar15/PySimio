import numpy as np


class Event:
    def __init__(self, time, bus, bus_stop, event_type):
        self.time = time
        self.bus = bus
        self.bus_stop = bus_stop
        self.type = event_type


class Map:
    def __init__(self, routes, buses, bus_stops):
        self.routes = routes
        self.buses = buses
        self.bus_stops = bus_stops
        self.event_queue = []

    def simulate(self, max_time):

        time = 0
        for bus in self.buses:
            # TODO: implement staggered departures
            self.event_queue.append(Event(0, bus, self.bus_stops['TDOG Depot'], 'departure'))

        while time < max_time:

            # sort the event queue
            sorted_queue = sorted(self.event_queue, key=lambda x: x.time)

            self.event_queue = sorted_queue[1:]
            next_event = sorted_queue[0]
            time = next_event.time

            # TODO: make this less stupid
            if time > max_time:
                break

            if next_event.type == "arrival":
                
                if next_event.bus_stop.name == "TDOG Depot":
                    # TODO: define the optimal policy to re-route buses
                    new_route = next_event.bus.route
                    next_event.bus.change_route(new_route)

                dpt_event = next_event.bus.arrive(next_event.bus_stop, next_event.time)
                self.event_queue.append(dpt_event)

            else:
                # TODO: calculate the delay time for the bus
                delay = 0
                arv_event = next_event.bus.depart(next_event.bus_stop, next_event.time, time + delay)
                self.event_queue.append(arv_event)


class Bus:
    """ Models a bus travelling around Ithaca.

    Attributes:
        route (Route): A Route object denoting which route this bus takes.
        next_stop_num (int): The stop number of the next stop this bus will stop at.
        next_stop (BusStop): A BusStop object denoting the next stop this bus will stop at.

        passengers (list): A list of Person objects representing the passengers on this bus.
        occupancy (int): The number of people currently on this bus.
        num_seats(int): The number of seats on this bus.
        standing_cap(int): The number of people that can be standing on this bus.
        max_cap(int): The maximum total capacity of this bus.

        distance (float): Total distance travelled by this bus

    """
    def __init__(self, route, name):

        assert(isinstance(route, Route)), "route must be a Route object"

        self.name = name
        self.route = route
        self.next_stop_num = 1                             # bus starts at first stop, i.e. index 0
        self.next_stop = self.route.stops[1]

        self.passengers = []                               # bus starts with nobody on it
        self.occupancy = 0
        self.num_seats = 25                                # default number of seats is 25
        self.standing_cap = 10                             # default standing capacity is 10
        self.max_cap = self.num_seats + self.standing_cap  # default total capacity is 25+10=35

        self.distance = 0                                  # distance travelled by this bus
        # TODO: other relevant performance metrics?

    def goes_to(self, stop):
        """Returns True if this bus goes to the specified stop and False otherwise"""

        assert(isinstance(stop, BusStop)), "stop must be a BusStop"
        return stop in self.route.stops

    def change_route(self, route):
        """Change the route that this bus travels on"""
        # TODO: implement better logic to find appropriate next stop
        self.route = route
        self.next_stop_num = 1
        self.next_stop = self.route.stops[1]

    def board(self, stop, time):
        # people waiting at bus stop will get on if bus goes to desired destination and there is space on the bus
        stop.update(time)
        boarding_time = time
        for person in stop.people_waiting:
            if self.goes_to(person.destination) and self.occupancy < self.max_cap:
                self.passengers.append(person)
                self.occupancy += 1

                stop.people_waiting.remove(person)
                stop.num_waiting -= 1

                person.waiting_time = boarding_time - person.start_time  # record waiting time
                boarding_time += np.random.triangular(0, 1 / 60, 5 / 60)  # boarding times have triangular distribution
                stop.update(boarding_time)  # people arrive while bus is boarding
                person.state = 'standing'
        return boarding_time

    def arrive(self, stop, time):
        """Models a bus arriving a BusStop stop at a given time"""

        assert(isinstance(stop, BusStop)), "must arrive at a BusStop"
        print('Arrived at', self.next_stop.name)
        self.next_stop_num = self.next_stop_num % (len(self.route.stops) - 1) + 1    # update next stop number
        self.next_stop = self.route.stops[self.next_stop_num]

        # if current stop is destination, passenger will get off
        for person in self.passengers:
            if person.destination == stop:
                self.passengers.remove(person)
                self.occupancy -= 1
                # TODO: add time taken for people to get off?
                person.state = 'arrived'
        print('After arrival, occupancy =', self.occupancy)

        return Event(time, self, stop, 'departure')

    def depart(self, stop, time, earliest_depart):
        """Models a bus driving from one stop to another"""

        distance_travelled = self.route.distances[self.next_stop_num - 1]
        self.distance += distance_travelled                # add distance travelled by bus

        if distance_travelled < 2:
            driving_time = (distance_travelled/20) * 60    # average speed of 20km/hr, convert to minutes
        else:
            driving_time = np.random.uniform(5, 7)         # average speed of 20km/hr, +/-1 min variability

        done_boarding = self.board(stop, time)
        if done_boarding < earliest_depart:
            done_boarding = self.board(stop, time)

        # first 25 passengers will sit down (or all, if less than 25 people on bus)
        for i in range(min(self.occupancy, 25)):
            self.passengers[i].state = 'sitting'

        return Event(done_boarding + driving_time, self, self.next_stop, 'arrival')


class BusStop:
    """ Models a bus stop somewhere in Ithaca.

    Attributes:
        name (str): Name of the bus stop.
        num_waiting (int): Number of people currently waiting at this bus stop.
        people_waiting (list): List of person objects representing people waiting at this bus stop

        times (dict): Dict of arrival times of people arriving at this bus stop

    """
    def __init__(self, name):

        self.name = name            # name of bus stop
        self.num_waiting = 0        # bus stop starts with nobody waiting
        self.people_waiting = []    # list of people waiting at this stop; initially empty
        self.times = {}             # dict of arrival times (key:destination, value:list of times)

    def add_data(self, times):
        self.times = times

    def arrival(self, person):
        """Models the arrival of a person to a bus stop"""
        self.num_waiting += 1
        self.people_waiting.append(person)

    def update(self, time):
        """Updates arrivals to this bus stop until a given time"""
        for destination, arrival_times in self.times.items():
            for arrival_time in arrival_times:
                if arrival_time < time:
                    self.arrival(Person(self, destination, arrival_time))
                    arrival_times.remove(arrival_time)
                else:
                    break


class Person:
    """ Models a person trying to get around Ithaca.

    Attributes:
        origin (BusStop): Where this person starts.
        destination (BusStop): Where this person is trying to get to.

        state (str): Describes state of person. One of 'waiting', 'sitting', 'standing', 'arrived'.
        start_time (float): Time at which person arrived at origin bus stop.
        waiting_time (float): Time spent waiting at origin bus stop.

    """
    def __init__(self, origin, destination, time):

        assert(isinstance(origin, BusStop)), "origin must be a BusStop"
        assert(isinstance(destination, BusStop)), "destination must be a BusStop"

        self.origin = origin               # origin bus stop
        self.destination = destination     # destination bus stop

        self.state = 'waiting'
        self.start_time = time             # time at which person started waiting
        self.waiting_time = 0              # time spent waiting at bus stop
        origin.arrival(self)


class Route:
    """ Models 1 of 3 bus routes around Ithaca.

    Attributes:
        stops (list): A list of BusStop objects representing all the stops on this route. Includes starting
            stop as both the first and last element if the route is a loop (which they all are).
        distances (list): A list of floats representing the distances between each of the stops on the route.
            Length should be one less than the length of stopList.
        num (int): Route number as defined in writeup.

    """
    def __init__(self, stop_list, distance_list, number):

        assert(all(isinstance(stop, BusStop) for stop in stop_list)), "stopList must be a list of BusStop objects"
        assert (len(distance_list) == len(stop_list) - 1), "Input arguments have wrong length!"

        self.stops = stop_list
        self.distances = distance_list
        self.num = number

        # TODO: all buses should start at Depot, including those on Route 2
