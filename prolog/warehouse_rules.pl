% Warehouse knowledge base: robots, packages, capabilities and priorities.

robot(r1).
robot(r2).
robot(r3).

package_type(p1, fragile).
package_type(p2, heavy).
package_type(p3, normal).

can_carry(r1, fragile).
can_carry(r1, normal).
can_carry(r2, heavy).
can_carry(r2, normal).
can_carry(r3, normal).
can_carry(r3, fragile).

priority(p1, high).
priority(p2, normal).
priority(p3, low).

valid_assignment(Robot, Package) :-
    robot(Robot),
    package_type(Package, Type),
    can_carry(Robot, Type).

high_priority_package(Package) :-
    priority(Package, high).

robots_for_package(Package, Robots) :-
    findall(R, valid_assignment(R, Package), Robots).

packages_for_robot(Robot, Packages) :-
    findall(P, valid_assignment(Robot, P), Packages).
