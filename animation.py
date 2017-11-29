import sys
import numpy as np
import pygame
from pySimio import *


def create_map(arrival_times=None):

    if arrival_times is None:
        rate = 5
        num_people = 20

        weg_e_com_e = list(np.cumsum(np.random.exponential(rate, num_people)))
        weg_e_ctown = list(np.cumsum(np.random.exponential(rate, num_people)))
        com_e_ctown = list(np.cumsum(np.random.exponential(rate, num_people)))
        ctown_com_w = list(np.cumsum(np.random.exponential(rate, num_people)))
        ctown_weg_w = list(np.cumsum(np.random.exponential(rate, num_people)))
        com_w_weg_w = list(np.cumsum(np.random.exponential(rate, num_people)))

    else:
        weg_e_com_e, weg_e_ctown, com_e_ctown, ctown_com_w, ctown_weg_w, com_w_weg_w = arrival_times

    depot = BusStop('TDOG Depot')
    weg_east = BusStop('Wegmans-Eastbound')
    weg_west = BusStop('Wegmans-Westbound')
    com_east = BusStop('Commons-Eastbound')
    com_west = BusStop('Commons-Westbound')
    ctown = BusStop('Collegetown')

    weg_east.add_data({com_east: weg_e_com_e, ctown: weg_e_ctown})
    com_east.add_data({ctown: com_e_ctown})
    com_west.add_data({weg_west: com_w_weg_w})
    ctown.add_data({com_west: ctown_com_w, weg_west: ctown_weg_w})

    # create a Route object for each of the 3 routes
    route1 = Route([depot, weg_east, com_east, ctown, com_west, weg_east, depot], [0.5, 2, 2, 2, 2, 0.5], 1)
    route2 = Route([com_east, ctown, com_west, com_east], [2, 2, 0.3], 2)
    route3 = Route([depot, weg_east, com_east, com_west, weg_west, depot], [0.5, 2, 2, 2, 0.5], 3)

    bus1 = Bus('Bus 1', route1)
    bus2 = Bus('The Kenta Bus', route2)

    return Map([route1, route2, route3], [bus1, bus2],
               {'TDOG Depot': depot, 'Wegmans-Eastbound': weg_east, 'Wegmans-Westbound': weg_west,
                'Commons-Eastbound': com_east, 'Commons-Westbound': com_west, 'Collegetown': ctown})


def make_button(picture, coords, surface):
    image = pygame.image.load(picture)
    image_rect = image.get_rect()
    image_rect.topleft = coords
    surface.blit(image, image_rect)
    return image, image_rect


def animate(map):

    pygame.init()
    size = width, height = 1080, 720
    screen = pygame.display.set_mode(size)

    # TODO: initialize map with all stops, route

    start = make_button('images/start.png', (width - 32 - 10, 10), screen)
    # TODO: pause, stop (reset) buttons

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse = pygame.mouse.get_pos()
                if start[1].collidepoint(mouse):
                    print('Start')
                    map.simulate(18*60)

        pygame.display.flip()

if __name__ == "__main__":
    ithaca = create_map()
    animate(ithaca)