You are checking short symbolic stories for continuity errors, the way one would
check a comic for a panel that contradicts what came before.

# World

Locations: hall, study, garden.
Characters: Jake, Marcus.
Objects: a lantern, a brass key.
Containers: a chest.

Initial state (before step 1 of every story):
- Jake is in the hall. Marcus is in the study.
- The lantern is lying on the floor of the hall, intact, held by nobody.
- The chest is in the study and is closed.
- The brass key is inside the closed chest, intact.

# What events mean

- move(actor, to): the actor walks to another location. Anything the actor is
  holding travels with them.
- take(actor, obj): the actor picks up an object. Only possible if the object is
  in the actor's location, held by nobody, and not inside a closed container.
- give(actor, obj, recipient): only possible if the actor is currently holding
  the object and both characters are in the same location.
- drop(actor, obj): the actor must be holding the object; it is left on the floor
  of the actor's current location.
- open(actor, container): the actor must be in the container's location and the
  container must be closed.
- break(actor, obj): the actor must be able to reach the object, which must be
  intact. It becomes broken.
- repair(actor, obj): the actor must be able to reach the object, which must be
  broken. It becomes intact.

# Rules

E-PRE  An event may only happen if its preconditions above hold.
I1     An object's location must equal the location of whoever or whatever holds
       it. An object cannot be in two places, or be held and inside a chest.
I2     No object may appear or vanish. The world always contains exactly the
       lantern and the key.
I3     An object's condition may only go from broken back to intact through an
       explicit repair event.
I4     An object inside a closed container cannot be acted on or leave it.
P1     Where a story states what a panel shows, the panel must agree with the
       state the events imply.

# Your task

For each story below, decide whether it is VALID (no rule is broken) or INVALID.
If it is INVALID, give the number of the FIRST step at which a rule is broken,
and which rule (E-PRE, I1, I2, I3, I4, or P1).

Answer as a table with one row per story: story letter, VALID/INVALID, first
violating step (or "-"), rule (or "-"), and one sentence of justification.
Do not write code. Reason directly about the stories.

## Story A

1. jake takes the lantern.
2. jake breaks the lantern.
3. jake moves to the study.
4. jake gives the lantern to marcus.
5. marcus opens the chest.
6. marcus takes the key.
7. marcus moves to the garden. The panel then shows: the lantern is intact.

## Story B

1. marcus opens the chest.
2. marcus takes the key. The panel then shows: the key is held by nobody; the key is inside the chest.
3. marcus moves to the hall.
4. marcus gives the key to jake.
5. jake moves to the garden.
6. jake drops the key.

## Story C

1. jake takes the lantern. The panel then shows: the lantern is held by jake; the lantern is in the hall.
2. jake moves to the garden. The panel then shows: jake is in the garden; the lantern is in the garden.
3. jake drops the lantern. The panel then shows: the lantern is held by nobody; the lantern is in the garden.
4. marcus opens the chest.
5. marcus takes the key. The panel then shows: the key is held by marcus; the key is not inside anything; the key is in the study.
6. marcus moves to the garden. The panel then shows: marcus is in the garden; the key is in the garden.

## Story D

1. jake takes the lantern.
2. jake moves to the study.
3. jake gives the lantern to marcus.
4. marcus opens the chest.
5. marcus takes the key.
6. marcus moves to the garden.
7. marcus drops the key.

## Story E

1. jake takes the lantern.
2. jake breaks the lantern.
3. jake moves to the study.
4. jake gives the lantern to marcus.
5. marcus opens the chest.
6. marcus takes the key.
7. marcus moves to the garden.
8. marcus repairs the lantern.

## Story F

1. marcus opens the chest.
2. marcus takes the key.
3. marcus moves to the hall.
4. marcus gives the key to jake.
5. jake moves to the garden.
6. jake drops the key. The panel then shows: the key is nowhere to be seen.

## Story G

1. jake takes the lantern.
2. jake moves to the study.
3. jake gives the lantern to marcus.
4. marcus opens the chest.
5. marcus takes the key.
6. jake moves to the hall.
7. jake moves to the garden.
8. jake gives the lantern to marcus.

## Story H

1. jake takes the lantern.
2. jake moves to the study.
3. marcus takes the lantern.
4. marcus moves to the garden.
5. marcus drops the lantern.
6. jake moves to the garden.

## Story I

1. marcus opens the chest.
2. marcus takes the key.
3. marcus moves to the hall.
4. marcus drops the key.
5. jake takes the key.
6. jake moves to the garden.
