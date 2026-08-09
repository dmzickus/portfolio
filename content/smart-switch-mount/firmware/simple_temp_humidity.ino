#include <DHT.h>
#define DHTPIN 2 // Pin connected to DATA, D$
#define DHTTYPE DHT11 // Define sensor type
DHT dht(DHTPIN, DHTTYPE);
void setup() {
 Serial.begin(9600);
 dht.begin();
}
void loop() {
 delay(2000); // Wait for sensor readings
 float humidity = dht.readHumidity();
 float temperatureC = dht.readTemperature();
 float temperatureF = dht.readTemperature(true);
 if (isnan(humidity) || isnan(temperatureC) || isnan(temperatureF)) {
   Serial.println("Failed to read from DHT11 sensor!");
   return;
 }
 Serial.print("Humidity: ");
 Serial.print(humidity);
 Serial.print("% | Temperature: ");
 Serial.print(temperatureC);
 Serial.print("°C ~ ");
 Serial.print(temperatureF);
 Serial.println("°F");
}