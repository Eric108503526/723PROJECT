import random

TIME_STEP = 2
NUM_SLOTS = 30
MAX_STEPS = 30

DIRECTIONS = ["N", "E", "S", "W"]

# ================================
# MAP DEFINITION
# ================================
NODES = ["A", "B", "C", "D"]
CLOCKWISE_DIR = {
    "A": "N",  # A -> B
    "B": "E",  # B -> C
    "C": "S",  # C -> D
    "D": "W",  # D -> A
}
COUNTERCLOCKWISE_DIR = {
    "A": "W",  # A -> D
    "D": "S",  # D -> C
    "C": "E",  # C -> B
    "B": "N",  # B -> A
}

def get_direction(current_node, next_node):
    """
    Return the first driving direction from current_node toward next_node.
    This simplified model assumes the vehicle moves along the outer ring.
    If both clockwise and counterclockwise are possible, choose clockwise.
    """
    if current_node == next_node:
        raise ValueError(f"current_node and next_node cannot be the same: {current_node}")

    cur_idx = NODES.index(current_node)
    next_idx = NODES.index(next_node)

    clockwise_steps = (next_idx - cur_idx) % len(NODES)
    counterclockwise_steps = (cur_idx - next_idx) % len(NODES)

    if clockwise_steps <= counterclockwise_steps:
        return CLOCKWISE_DIR[current_node]
    else:
        return COUNTERCLOCKWISE_DIR[current_node]

# ================================
# VEHICLE MODEL
# ================================
class Vehicle:
    def __init__(self, vid, start, start_slot=0):
        self.vehicle_id = vid

        # Randomize intermediate nodes for more dynamic routes
        nodes = ["B", "C", "D"]
        random.shuffle(nodes)
        # Route: start -> random nodes -> start (loop)
        self.route = ["A"] + nodes + ["A"]

        self.route_idx = self.route.index(start)
        self.current_node = start
        self.next_node = self.route[self.route_idx + 1]

        # Determine initial direction based on route
        self.direction = get_direction(self.current_node, self.next_node)

        # Lane representation (simplified single intersection model)
        self.lane = f"{self.current_node}_to_I1"
        self.slot = start_slot

        # Dynamic states
        self.speed = 0
        self.wait_time = 0
        self.finished = False

    def update_direction(self):
        """
        Update vehicle direction based on current route position.
        """
        self.direction = get_direction(self.current_node, self.next_node)

    def advance_route(self):
        """
        Move to the next segment in the route after crossing an intersection.
        """
        self.route_idx += 1

        # If route completed, mark as finished
        if self.route_idx == len(self.route) - 1:
            self.finished = True
            return

        self.current_node = self.route[self.route_idx]
        self.next_node = self.route[self.route_idx + 1]

        self.update_direction()

        # Update lane after moving to next segment
        self.lane = f"{self.current_node}_to_I1"

    def to_dict(self):
        """
        Convert vehicle state to dictionary format (Phase B protocol).
        """
        return {
            "vehicle_id": self.vehicle_id,
            "lane": self.lane,
            "slot": self.slot,
            "direction": self.direction,
            "speed": self.speed,
            "wait_time": self.wait_time
        }

# ================================
# MOCK SIGNAL CONTROLLER (Phase A)
# ================================
def mock_signal(t):
    """
    Generate a simple round-robin traffic signal.
    This simulates the i-group behavior in Phase A.
    """
    return {
        "green_direction": DIRECTIONS[t % 4]
    }

# ================================
# HELPER FUNCTIONS
# ================================
def front_blocked(v, vehicles):
    """
    Check if there is a vehicle directly in front (same lane, next slot).
    """
    for o in vehicles:
        if o.vehicle_id != v.vehicle_id and o.lane == v.lane:
            if o.slot == v.slot + 1:
                return True
    return False


def congestion_level(v, vehicles):
    """
    Count how many vehicles are ahead in the same lane.
    Used as a simple congestion metric.
    """
    count = 0
    for o in vehicles:
        if o.lane == v.lane and o.slot > v.slot:
            count += 1
    return count


# ================================
# DECISION LOGIC
# ================================
def decide(v, vehicles, signal):
    """
    Determine vehicle action (move or stop) based on:
    - congestion
    - front vehicle
    - traffic signal
    """

    if v.finished:
        v.speed = 0
        return

    # Stop if congestion ahead is too high
    if congestion_level(v, vehicles) >= 3:
        v.speed = 0
        v.wait_time += 1
        return

    # Stop if directly blocked by another vehicle
    if front_blocked(v, vehicles):
        v.speed = 0
        v.wait_time += 1
        return

    # At intersection: obey traffic signal
    if v.slot == NUM_SLOTS - 1:
        if v.direction == signal["green_direction"]:
            v.speed = 1
            v.wait_time = 0
        else:
            v.speed = 0
            v.wait_time += 1
        return

    # Otherwise, move forward normally
    v.speed = 1
    v.wait_time = 0


# ================================
# MOVEMENT LOGIC
# ================================
def move(v):
    """
    Update vehicle position based on speed.
    Handles both lane movement and intersection crossing.
    """
    if v.finished:
        return

    if v.speed == 1:
        if v.slot < NUM_SLOTS - 1:
            v.slot += 1
        else:
            # Crossing the intersection
            v.slot = 0
            v.advance_route()


# ================================
# SAFETY CHECKS
# ================================
def check_collision(vehicles):
    """
    Detect collisions: more than one vehicle occupying the same lane/slot.
    """
    seen = set()
    collisions = 0

    for v in vehicles:
        if v.finished:
            continue

        key = (v.lane, v.slot)
        if key in seen:
            collisions += 1
        seen.add(key)

    return collisions


def check_illegal_direction(v):
    """
    Check if vehicle direction is invalid.
    """
    return v.direction not in DIRECTIONS


def check_uturn(v):
    """
    Placeholder for U-turn detection (not implemented in Phase A).
    """
    return False


# ================================
# MAIN SIMULATION STEP
# ================================
def step(vehicles, signal):
    """
    Perform one simulation step:
    1. Decide actions
    2. Update positions
    """

    for v in vehicles:
        decide(v, vehicles, signal)

    for v in vehicles:
        move(v)

    return vehicles


# ================================
# SIMULATION DRIVER
# ================================
def run():
    """
    Run the full simulation and print results.
    """

    vehicles = [
        Vehicle(1, "A", start_slot=0),
        Vehicle(2, "A", start_slot=2),
        Vehicle(3, "A", start_slot=4),
    ]

    total_collision = 0

    for t in range(MAX_STEPS):

        signal = mock_signal(t)

        vehicles = step(vehicles, signal)

        collision = check_collision(vehicles)
        total_collision += collision

        print(f"\nTime {t}")
        print("Signal:", signal)

        for v in vehicles:
            print(v.to_dict())

        print("Collision:", collision)

    print("\nTotal collision:", total_collision)

if __name__ == "__main__":
    run()