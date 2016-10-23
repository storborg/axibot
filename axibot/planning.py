import math

from . import config, moves


def v_final_vi_a_dx(v_initial, accel, dx):
    """
    Kinematic calculation: Final velocity with constant linear acceleration.

    Calculate and return the (real) final velocity, given an initial velocity,
    acceleration rate, and distance interval.

    Uses the kinematic equation Vf^2 = 2 a D_x + Vi^2, where
            Vf is the final velocity,
            a is the acceleration rate,
            D_x (delta x) is the distance interval, and
            Vi is the initial velocity.

    We are looking at the positive root only-- if the argument of the sqrt is
    less than zero, return -1, to indicate a failure.
    """
    final_v_sq = (2 * accel * dx) + (v_initial**2)
    if (final_v_sq > 0):
        return math.sqrt(final_v_sq)
    else:
        return -1


def v_initial_vf_a_dx(v_final, accel, dx):
    """
    Kinematic calculation: Maximum allowed initial velocity to arrive at
    distance X with specified final velocity, and given maximum linear
    acceleration.

    Calculate and return the (real) initial velocity, given an final velocity,
    acceleration rate, and distance interval.

    Uses the kinematic equation Vi^2 = Vf^2 - 2 a D_x , where
            Vf is the final velocity,
            a is the acceleration rate,
            D_x (delta x) is the distance interval, and
            Vi is the initial velocity.

    We are looking at the positive root only-- if the argument of the sqrt is
    less than zero, return -1, to indicate a failure.
    """
    initial_v_sq = (v_final**2) - (2 * accel * dx)
    if (initial_v_sq > 0):
        return math.sqrt(initial_v_sq)
    else:
        return -1


def dot_product_xy(a, b):
    temp = a[0] * b[0] + a[1] * b[1]
    if (temp > 1):
        return 1
    elif (temp < -1):
        return -1
    else:
        return temp


def plot_segment_with_velocity(xy, v_initial, v_final, pen_up):
    """
    Generate the low-level machine moves to plot a straight line segment, with
    a trapezoidal velocity profile. That is, ramp velocity up to v_final,
    starting from v_initial, move at a constant v_final, then ramp velocity
    back down to v_initial.

    Units are inches (for position points) or inches per second (for velocity).
    Note that position inputs to this function is differential: it only moves
    relative to the existing position of the robot.
    """
    # XXX This function is abysmal and could use a lot of cleanup. But maybe
    # write some tests first.

    # Steps per inch of microstepping.
    spi = config.DPI_16X

    # XXX should this check bounds limits??

    # convert to motor step units
    x, y = xy
    xmove_ideal = spi * x
    ymove_ideal = spi * y
    v_initial *= spi
    v_final *= spi

    motor_steps1 = int(round(xmove_ideal + ymove_ideal))
    motor_steps2 = int(round(xmove_ideal - ymove_ideal))

    plot_distance = math.sqrt((motor_steps1**2) + (motor_steps2**2))
    if plot_distance < 1.0:
        return []

    # Get limits based on pen up/down state.
    if (not pen_up) or (plot_distance < (spi * config.SHORT_THRESHOLD)):
        speed = config.SPEED_PEN_DOWN
        accel_rate = speed / config.ACCEL_TIME_PEN_DOWN
    else:
        speed = config.SPEED_PEN_UP
        accel_rate = speed / config.ACCEL_TIME_PEN_UP

    # Obey the speed limit plz
    v_initial = min(v_initial, speed)
    v_final = min(v_final, speed)

    # Times to reach maximum speed, from our initial velocity
    # vMax = vi + a*t  =>  t = (vMax - vi)/a
    # vf = vMax - a*t   =>  t = -(vf - vMax)/a = (vMax - vf)/a
    # -- These are _maximum_ values. We often do not have enough time/space to
    # reach full speed.
    t_accel = (speed - v_initial) / accel_rate
    t_decel = (speed - v_final) / accel_rate

    # Distance required to reach full speed, from start at speed v_initial
    accel_dist = (v_initial * t_accel) + (0.5 * accel_rate * (t_accel**2))
    decel_dist = (v_final * t_decel) + (0.5 * accel_rate * (t_decel**2))

    # Slice travel into slices of time that are at least 50ms long
    timeslice = config.TIME_SLICE

    time_elapsed = 0.0
    position = 0.0
    velocity = v_initial

    duration_array = []
    distance_array = []

    if plot_distance > (accel_dist + decel_dist + timeslice * speed):
        # Make a trapezoid velocity profile
        print("trapezoidal velocity profile")

        print("accel phase, t_accel:%s, timeslice:%s" % (t_accel, timeslice))
        intervals = int(math.floor(t_accel / timeslice))
        if intervals:
            interval_time = t_accel / intervals
            velocity_step = (speed - v_initial) / (intervals + 1.0)
            for ii in range(intervals):
                print("  step")
                velocity += velocity_step
                time_elapsed += interval_time
                position += velocity * interval_time
                duration_array.append(int(round(time_elapsed * 1000.0)))
                # distance along the line of travel
                distance_array.append(position)

        print("coast phase")
        coast_distance = plot_distance - (accel_dist + decel_dist)
        if coast_distance > (timeslice * speed):
            velocity = speed
            cruising_time = coast_distance / velocity
            time_elapsed += cruising_time
            duration_array.append(int(round(time_elapsed * 1000.0)))
            position += velocity * cruising_time
            distance_array.append(position)

        print("decel phase, t_decel:%s, timeslice:%s" % (t_decel, timeslice))
        intervals = int(math.floor(t_decel / timeslice))
        if intervals:
            interval_time = t_decel / intervals
            velocity_step = (speed - v_final) / (intervals + 1.0)
            for ii in range(intervals):
                print("  step")
                velocity -= velocity_step
                time_elapsed += interval_time
                position += velocity * interval_time
                duration_array.append(int(round(time_elapsed * 1000.0)))
                # distance along the line of travel
                distance_array.append(position)

    else:
        # Make a triangle velocity profile
        ta = ((math.sqrt(2 * v_initial * v_initial + 2 *
                         v_final * v_final + 4 *
                         accel_rate * plot_distance) - 2 * v_initial) /
              (2 * accel_rate))

        if (ta < 0):
            ta = 0

        v_max = v_initial + accel_rate * ta

        # Number of intervals during acceleration
        intervals = int(math.floor(ta / timeslice))

        if (intervals == 0):
            ta = 0
        td = ta - (v_final - v_initial) / accel_rate
        # Number of intervals during acceleration
        d_intervals = int(math.floor(td / timeslice))

        if ((intervals + d_intervals) > 4):
            print("triangular velocity profile")
            if (intervals > 0):
                time_per_interval = ta / intervals
                velocity_step = (
                    v_max - v_initial) / (intervals + 1.0)
                # For six time intervals of acceleration, first interval is at
                # velocity (max/7)
                # 6th (last) time interval is at 6*max/7
                # after this interval, we are at full speed.

                # Calculate acceleration phase
                for index in range(0, intervals):
                    velocity += velocity_step
                    time_elapsed += time_per_interval
                    position += velocity * time_per_interval
                    duration_array.append(
                        int(round(time_elapsed * 1000.0)))
                    # Estimated distance along direction of travel
                    distance_array.append(position)

            if (d_intervals > 0):
                time_per_interval = td / d_intervals
                velocity_step = (
                    v_max - v_final) / (d_intervals + 1.0)
                # For six time intervals of acceleration, first interval is at
                # velocity (max/7)
                # 6th (last) time interval is at 6*max/7
                # after this interval, we are at full speed.

                # Calculate acceleration phase
                for index in range(0, d_intervals):
                    velocity -= velocity_step
                    time_elapsed += time_per_interval
                    position += velocity * time_per_interval
                    duration_array.append(
                        int(round(time_elapsed * 1000.0)))
                    # Estimated distance along direction of travel
                    distance_array.append(position)
        else:
            print("linear velocity profile")
            # linear velocity change
            # xFinal = vi * t  + (1/2) a * t^2, and vFinal = vi + a * t
            # Combining these (with same t) gives:
            # 2 a x = (vf^2 - vi^2)  => a = (vf^2 - vi^2)/2x
            # So long as this 'a' is less than accel_rate, we can
            # linearly interpolate in velocity.

            # Boost initial speed for this segment
            v_initial = (v_max + v_initial) / 2
            velocity = v_initial  # Boost initial speed for this segment

            local_accel = ((v_final * v_final - v_initial * v_initial) /
                           (2.0 * plot_distance))

            if (local_accel > accel_rate):
                local_accel = accel_rate
            elif (local_accel < -accel_rate):
                local_accel = -accel_rate
            if local_accel != 0:
                t_segment = (v_final - v_initial) / local_accel

            # Number of intervals during deceleration
            intervals = int(math.floor(t_segment / timeslice))
            if (intervals > 1):
                time_per_interval = t_segment / intervals
                velocity_step = (
                    v_final - v_initial) / (intervals + 1.0)
                # For six time intervals of acceleration, first interval is at
                # velocity (max/7)
                # 6th (last) time interval is at 6*max/7
                # after this interval, we are at full speed.

                # Calculate acceleration phase
                for index in range(0, intervals):
                    velocity += velocity_step
                    time_elapsed += time_per_interval
                    position += velocity * time_per_interval
                    duration_array.append(
                        int(round(time_elapsed * 1000.0)))
                    # Estimated distance along direction of travel
                    distance_array.append(position)
            else:
                # Short segment; Not enough time for multiple segments
                # at different velocities.
                # These are _slow_ segments-- use fastest possible
                # interpretation.
                v_initial = v_max

    dest_array1 = []
    dest_array2 = []
    prev_motor1 = 0
    prev_motor2 = 0
    prev_time = 0

    # given time & distance motion arrays, compute actual moves
    for ii in range(len(distance_array)):
        frac_distance = distance_array[ii] / position
        dest_array1.append(int(round(frac_distance * motor_steps1)))
        dest_array2.append(int(round(frac_distance * motor_steps2)))

    prev_motor1 = 0
    prev_motor2 = 0
    prev_time = 0

    actions = []

    for ii in range(len(dest_array1)):
        move_steps1 = dest_array1[ii] - prev_motor1
        move_steps2 = dest_array2[ii] - prev_motor2
        move_time = duration_array[ii] - prev_time
        prev_time = duration_array[ii]

        # don't allow zero-time moves.
        if (move_time < 1):
            move_time = 1

        # don't allow too-slow movements of this axis
        if (abs((float(move_steps1) / float(move_time))) < 0.002):
            move_steps1 = 0
        if (abs((float(move_steps2) / float(move_time))) < 0.002):
            move_steps2 = 0

        prev_motor1 += move_steps1
        prev_motor2 += move_steps2

        # if at least one motor step is required for this move....
        if move_steps1 or move_steps2:
            actions.append(moves.XYMove(move_steps1, move_steps2, move_time))

    return actions


def plan_trajectory(path, pen_up):
    """
    Generate the sequence of moves for a full path, accounting for
    acceleration.

    The input path is an ordered list of (x, y) pairs to cover, in the
    coordinate space of the document, not in the coordinate space of the
    motors. Units are in inches.

    Coordinates are 'absolute', but the move to the beginning of the path will
    not be generated, so the caller of this function is responsible for
    ensuring that paths are linked: that is, the first point of a path must be
    the last path of the previous path.
    """
    assert len(path) >= 2

    # XXX check bounds here??

    if len(path) == 2:
        # Just a straight line, skip trajectory planning
        return plot_segment_with_velocity(path[0], path[1], 0, 0,
                                          pen_up=pen_up)

    traj_length = len(path)

    traj_distances = []
    traj_velocities = []
    traj_vectors = []

    traj_distances.append(0.0)
    traj_velocities.append(0.0)

    for i in range(1, traj_length):
        # Distance per segment:
        xdist = path[i][0] - path[i - 1][0]
        ydist = path[i][1] - path[i - 1][1]
        tmp_dist = math.sqrt((xdist**2) + (ydist**2))
        traj_distances.append(tmp_dist)
        # Normalized unit vectors:
        if (tmp_dist == 0):
            tmp_dist = 1
        tmp_x = (path[i][0] - path[i - 1][0]) / tmp_dist
        tmp_y = (path[i][1] - path[i - 1][1]) / tmp_dist
        traj_vectors.append([tmp_x, tmp_y])

    if pen_up:
        # speed limit in this state
        speed = config.SPEED_PEN_UP
        # time to reach full speed (from zero), at maximum acceleration.
        t_max = config.ACCEL_TIME_PEN_UP
    else:
        speed = config.SPEED_PEN_DOWN
        t_max = config.ACCEL_TIME_PEN_DOWN

    # acceleration/deceleration rate: (Maximum speed) / (time to reach that
    # speed)
    accel_rate = speed / t_max

    # Distance that is required to reach full speed, from zero speed:
    # (1/2) a t^2
    accel_dist = 0.5 * accel_rate * t_max * t_max

    '''
    Now, step through every vertex in the trajectory, and calculate what the
    speed should be when arriving at that vertex.

    In order to do so, we need to understand how the trajectory will evolve in
    terms of position and velocity for a certain amount of time in the future,
    past that vertex.  The most extreme cases of this is when we are traveling
    at full speed initially, and must come to a complete stop.
        (This is actually more sudden than if we must reverse course-- that
        must also go through zero velocity at the same rate of deceleration,
        and a full reversal that does not occur at the path end might be able
        to have a nonzero velocity at the endpoint.)

    Thus, we look ahead from each vertex until one of the following occurs:
        (1) We have looked ahead by at least t_max, or
        (2) We reach the end of the path.

    The data that we have to start out with is this:
        - The position and velocity at the previous vertex
        - The position at the current vertex
        - The position at subsequent vertices
        - The velocity at the final vertex (zero)

    To determine the correct velocity at each vertex, we will apply the
    following rules:

    (A) For the first point, V(i = 0) = 0.

    (B) For the last point point, Vi = 0 as well.

    (C) If the length of the segment is greater than the distance
    required to reach full speed, then the vertex velocity may be as
    high as the maximum speed.

    (D) However, if the length of the segment is less than the total distance
    required to get to full speed, then the velocity at that vertex
    is limited by to the value that can be reached from the initial
    starting velocity, in the distance given.

    (E) The maximum velocity through the junction is also limited by the
    turn itself-- if continuing straight, then we do not need to slow down
    as much as if we were fully reversing course.
    We will model each corner as a short curve that we can accelerate around.

    (F) To calculate the velocity through each turn, we must _look ahead_ to
    the subsequent (i+1) vertex, and determine what velocity
    is appropriate when we arrive at the next point.

    Because future points may be close together-- the subsequent vertex could
    occur just before the path end -- we actually must look ahead past the
    subsequent (i + 1) vertex, all the way up to the limits that we have
    described (e.g., t_max) to understand the subsequent behavior. Once we have
    that effective endpoint, we can work backwards, ensuring that we will be
    able to get to the final speed/position that we require.

    A less complete (but far simpler) procedure is to first complete the
    trajectory description, and then -- only once the trajectory is complete --
    go back through, but backwards, and ensure that we can actually decelerate
    to each velocity.

    (G) The minimum velocity through a junction may be set to a constant.
    There is often some (very slow) speed -- perhaps a few percent of the
    maximum speed at which there are little or no resonances. Even when the
    path must directly reverse itself, we can usually travel at a non-zero
    speed. This, of course, presumes that we still have a solution for getting
    to the endpoint at zero speed.
    '''

    # Corner rounding/tolerance factor-- not sure how high this should be
    # set.
    delta = config.CORNERING / 1000

    for i in range(1, traj_length - 1):
        # Length of the segment leading up to this vertex
        d_current = traj_distances[i]
        # Velocity when leaving previous vertex
        v_prev_exit = traj_velocities[i - 1]

        '''
        Velocity at vertex: Part I

        Check to see what our plausible maximum speeds are, from
        acceleration only, without concern about cornering, nor deceleration.
        '''

        if (d_current > accel_dist):
            # There _is_ enough distance in the segment for us to either
            # accelerate to maximum speed or come to a full stop before
            # this vertex.
            v_current_max = speed
        else:
            # There is _not necessarily_ enough distance in the segment for us
            # to either accelerate to maximum speed or come to a full stop
            # before this vertex. Calculate how much we *can* swing the
            # velocity by:

            v_current_max = v_final_vi_a_dx(v_prev_exit, accel_rate, d_current)
            if (v_current_max > speed):
                v_current_max = speed

        '''
        Velocity at vertex: Part II

        Assuming that we have the same velocity when we enter and leave a
        corner, our acceleration limit provides a velocity that depends upon
        the angle between input and output directions.

        The cornering algorithm models the corner as a slightly smoothed
        corner, to estimate the angular acceleration that we encounter:
            https://onehossshay.wordpress.com/2011/09/24/
                improving_grbl_cornering_algorithm/

        The dot product of the unit vectors is equal to the cosine of the angle
        between the two unit vectors, giving the deflection between the
        incoming and outgoing angles.  Note that this angle is (pi - theta), in
        the convention of that article, giving us a sign inversion.
            [cos(pi - theta) = - cos(theta)]
        '''

        cosine_factor = -dot_product_xy(traj_vectors[i - 1], traj_vectors[i])

        root_factor = math.sqrt((1 - cosine_factor) / 2)
        denominator = 1 - root_factor
        if (denominator > 0.0001):
            Rfactor = (delta * root_factor) / denominator
        else:
            Rfactor = 100000
        v_junction_max = math.sqrt(accel_rate * Rfactor)

        if (v_current_max > v_junction_max):
            v_current_max = v_junction_max

        # "Forward-going" speed limit for velocity at this particular vertex.
        traj_velocities.append(v_current_max)

    # Add zero velocity, for final vertex.
    traj_velocities.append(0.0)

    '''
    Velocity at vertex: Part III

    We have, thus far, ensured that we could reach the desired velocities,
    going forward, but have also assumed an effectively infinite deceleration
    rate.

    We now go through the completed array in reverse, limiting velocities to
    ensure that we can properly decelerate in the given distances.
    '''

    for j in range(1, traj_length):
        i = traj_length - j    # Range: From (traj_length - 1) down to 1.

        v_final = traj_velocities[i]
        v_initial = traj_velocities[i - 1]
        segment_length = traj_distances[i]

        if (v_initial > v_final) and (segment_length > 0):
            v_init_max = v_initial_vf_a_dx(
                v_final, -accel_rate, segment_length)

            if (v_init_max < v_initial):
                v_initial = v_init_max
            traj_velocities[i - 1] = v_initial

    # XXX It might make sense to refactor this function so that it just returns
    # a list of (start_point, end_point, initial_velocity, final_velocity)
    # tuples, so that it can be tested in isolation.

    actions = []
    for i in range(1, traj_length):
        dx = path[i][0] - path[i - 1][0]
        dy = path[i][1] - path[i - 1][1]
        actions.extend(plot_segment_with_velocity((dx, dy),
                                                  traj_velocities[i - 1],
                                                  traj_velocities[i],
                                                  pen_up=pen_up))
    return actions
