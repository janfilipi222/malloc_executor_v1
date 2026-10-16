
from domain.hardware.hardware_model import Joint
from math import *



def _calculate_3Dof_IK(target: list[float], joints):
    x, y, z = target
    t = sqrt(x**2 + z**2)
    alpha = atan2(x, -z) * -1
    # print("alpha: " , alpha, x, z, -z)

    y *= -1
    y += joints[0].length


    len_1 = joints[1].length
    len_2 = joints[2].length + joints[3].length

    # print("lengths: ", len_1, len_2)


    # x_w = t
    # y_w = y

    # print(t)

    l = sqrt(t**2 + y**2)
    epsilon = atan2(y, t)

    print(l)
    print(len_1)
    print(len_2)

    theta1 = acos((len_1**2 + l**2 - len_2**2) / (2 * len_1 * l))
    theta2 = acos((len_1**2 + len_2**2 - l**2) / (2 * len_1 * len_2))

    print(degrees(theta1), degrees(theta2))

    alpha_prime = epsilon - theta1 + pi / 2
    beta_prime = pi - theta2

    print(
        degrees(alpha),
        degrees(alpha_prime),
        degrees(beta_prime)
    )

    return alpha, alpha_prime, beta_prime


def calculate_4DoF_IK(target: list[float], target_phi: float, joints):
    x, y, z = target
    t = sqrt(x**2 + z**2)
    alpha = atan2(x, -z) * -1
    # print("alpha: " , alpha, x, z, -z)

    y *= -1
    y += joints[0].length


    len_1 = joints[1].length
    len_2 = joints[2].length + joints[3].length
    len_3 = joints[4].length

    # print("lengths: ", len_1, len_2)

    x_w = t - len_3 * cos(target_phi)
    y_w = y - len_3 * sin(target_phi)

    # x_w = t
    # y_w = y

    # print(t)

    l = sqrt(x_w**2 + y_w**2)
    epsilon = atan2(y_w, x_w)

    theta1 = acos((len_1**2 + l**2 - len_2**2) / (2 * len_1 * l))
    theta2 = acos((len_1**2 + len_2**2 - l**2) / (2 * len_1 * len_2))

    alpha_prime = epsilon - theta1 + pi / 2
    beta_prime = pi - theta2



    theta_3 = target_phi - (alpha_prime + beta_prime) + pi / 2

    # print(
    #     degrees(alpha),
    #     degrees(alpha_prime),
    #     degrees(beta_prime),
    #     degrees(theta_3),
    # )

    return alpha, alpha_prime, beta_prime, theta_3

    joint1.angle = alpha_prime
    joint2.angle = beta_prime
    joint3.angle = theta_3
