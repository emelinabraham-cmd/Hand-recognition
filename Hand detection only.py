import cv2
import mediapipe as mp
import time

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

# finger tip indexes
finger_tips = [4, 8, 12, 16, 20]

def count_fingers(hand_landmarks):
    fingers = []

    # Thumb (image flipped)
    if hand_landmarks.landmark[4].x > hand_landmarks.landmark[3].x:
        fingers.append(1)
    else:
        fingers.append(0)

    # Other fingers
    for tip in [8, 12, 16, 20]:
        if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[tip - 2].y:
            fingers.append(1)
        else:
            fingers.append(0)

    return sum(fingers)


cap = cv2.VideoCapture(0)

state = 0
first_num = None
second_num = None
operand = None

stable_count = 0
stable_value = None

with mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.6) as hands:
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)

        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(image)

        finger_number = None

        if result.multi_hand_landmarks:
            for hand in result.multi_hand_landmarks:
                mp_draw.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)
                finger_number = count_fingers(hand)

        # Stabilize finger reading
        if finger_number == stable_value:
            stable_count += 1
        else:
            stable_value = finger_number
            stable_count = 1

        accepted = (stable_count >= 20 and stable_value is not None)

        # -----------------------------
        # Calculator Flow (States)
        # -----------------------------
        if state == 0:
            cv2.putText(frame, "Show FIRST number (1-5)", (20, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)

            if accepted:
                first_num = stable_value
                state = 1
                stable_count = 0

        elif state == 1:
            cv2.putText(frame, "Show SECOND number (1-5)", (20, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)

            if accepted:
                second_num = stable_value
                state = 2
                stable_count = 0

        elif state == 2:
            cv2.putText(frame, "Operator (1:+   2:-   3:*   4:/)", (10, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)

            if accepted:
                fingers = stable_value

                if fingers == 1:
                    operand = "+"
                elif fingers == 2:
                    operand = "-"
                elif fingers == 3:
                    operand = "*"
                elif fingers == 4:
                    operand = "/"
                else:
                    operand = None

                if operand is not None:
                    state = 3
                    stable_count = 0

        elif state == 3:
            expr = f"{first_num} {operand} {second_num}"

            try:
                result_value = eval(expr)
            except:
                result_value = "ERROR"

            cv2.putText(frame, f"Result: {expr} = {result_value}", (20, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)

            cv2.putText(frame, "Press R to restart|Press esc to stop", (20, 100),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,255), 2)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('r'):
                state = 0
                first_num = None
                second_num = None
                operand = None
                stable_count = 0

        cv2.imshow("Finger Calculator", frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break

cap.release()
cv2.destroyAllWindows()
