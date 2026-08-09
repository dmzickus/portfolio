const int rPin = 15;
const int gPin = 13;
const int bPin = 12;
const int button = 0;

const char* modes[] = {"none", "christmas", "usa", "rgb", "secondary"};
const int size = sizeof(modes) / sizeof(modes[0]);
int mode = 3;

unsigned long waiter = millis();
unsigned long wait_time = 500;

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  pinMode(rPin, OUTPUT);
  pinMode(gPin, OUTPUT);
  pinMode(bPin, OUTPUT);
  pinMode(button, INPUT_PULLUP);

  digitalWrite(rPin, HIGH);
  digitalWrite(gPin, HIGH);
  digitalWrite(bPin, HIGH);
}

// The events to listen to while we are waiting inside listen(x)
// Again the responses to these events cannot take time
// But you can listen to buttons, inputs, mqtt, etc.
bool listeners() {
  bool event = false;
  if (!digitalRead(button)) {
    mode = (mode + 1) % size;
    Serial.print("Mode ");
    Serial.print(mode);
    Serial.print(": ");
    Serial.println(modes[mode]);
    waiter = millis();
    event = true;
  }
  return event;
}

// When calling delay(x) in the effect functions, the program halts
// We want to be able to listen for button inputs (and maybe later mqtt inputs)
// While we are putting on the show, so we must improvise
// Basically just listen to the buttons until the time runs out
bool listen(unsigned long wait_time) {
  unsigned long start = millis();
  bool event = false;
  while (millis() - start > wait_time && ! event) {
    // Here we can listen for whatever we want
    // When an event occurs, the response cannot take time
    // We are working with milliseconds here people
    event = listeners();
  }
  Serial.println(event);
  return event;
}

// *** MACROS ***
  // Remember this is a macro, not a function, it replaces the macro call with this exact code
  // So no using the below variable names:
    // 'end', 'event'
  // Also only call the macro with no trailing semicolon
    // 'LISTEN(500)'
  // Also because it is a macro, something weird could happen
  // Also, no type checking
  // Single line if...
#define LISTEN(wait_time) if (listen(wait_time)) return;


void noneColors() {
  digitalWrite(rPin, HIGH);
  digitalWrite(gPin, HIGH);
  digitalWrite(bPin, HIGH);
  LISTEN(1);
}

void rgbColors() {
  noneColors();
  // RGB Colors
  digitalWrite(rPin, LOW);
  digitalWrite(bPin, HIGH);
  LISTEN(333);
  digitalWrite(gPin, LOW);
  digitalWrite(rPin, HIGH);
  LISTEN(333);
  digitalWrite(bPin, LOW);
  digitalWrite(gPin, HIGH);
  LISTEN(333);
}

void usaColors() {
  noneColors();
  // USA Colors
  digitalWrite(rPin, LOW);
  digitalWrite(bPin, HIGH);
  LISTEN(500);
  digitalWrite(rPin, LOW);
  digitalWrite(gPin, LOW);
  digitalWrite(bPin, LOW);
  LISTEN(500);
  digitalWrite(rPin, HIGH);
  digitalWrite(gPin, HIGH);
  LISTEN(500);
}

void secondaryColors() {
  noneColors();
  // Secondary Colors
  for (int i = 0; i <= 255 / 2; i++) {
    analogWrite(bPin, i);
    analogWrite(rPin, 255 - i);
    LISTEN(10);
  }
  for (int i = 0; i <= 255 / 2; i++) {
    analogWrite(rPin, i);
    analogWrite(gPin, 255 - i);
    LISTEN(10);
  }
  for (int i = 0; i <= 255 / 2; i++) {
    analogWrite(gPin, i);
    analogWrite(bPin, 255 - i);
    LISTEN(10);
  }
}

void christmasColors() {
  noneColors();
  // Christmas Colors
  for (int i = 0; i <= 255; i++) {
    analogWrite(rPin, 128 - i);
    LISTEN(5);
  }
  for (int i = 0; i <= 255; i++) {
    analogWrite(rPin, i);
    LISTEN(5);
  }
  digitalWrite(rPin, HIGH);
  for (int i = 0; i <= 255 / 4; i++) {
    analogWrite(gPin, 255 - i);
    LISTEN(20);
  }
  for (int i = 192; i <= 255; i++) {
    analogWrite(gPin, i);
    LISTEN(20);
  }
  digitalWrite(gPin, HIGH);
}

void loop() {
  switch (mode) {
    case 1:
      christmasColors();
      break;
    case 2:
      usaColors();
      break;
    case 3:
      rgbColors();
      break;
    case 4:
      secondaryColors();
      break;
    case 0:
    default:
    noneColors();
      break;
  }
}
