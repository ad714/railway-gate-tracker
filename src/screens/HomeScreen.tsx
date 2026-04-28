import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TextInput, Pressable, Alert, Dimensions } from 'react-native';
import MapView, { PROVIDER_GOOGLE } from 'react-native-maps';
import * as Location from 'expo-location';
import { COLORS, TYPOGRAPHY, SHAPES } from '../theme/tokens';

interface HomeScreenProps {
  onSearch: (details: { origin: string; destination: string }) => void;
}

const { width, height } = Dimensions.get('window');

const HomeScreen: React.FC<HomeScreenProps> = ({ onSearch }) => {
  const [locationGranted, setLocationGranted] = useState<boolean>(false);
  const [origin, setOrigin] = useState<string>('Current Location');
  const [destination, setDestination] = useState<string>('');
  const [currentRegion, setCurrentRegion] = useState({
    latitude: 19.12,
    longitude: 72.93,
    latitudeDelta: 0.15,
    longitudeDelta: 0.15,
  });

  useEffect(() => {
    requestLocationPermission();
  }, []);

  const requestLocationPermission = async () => {
    let { status } = await Location.requestForegroundPermissionsAsync();
    if (status !== 'granted') {
      return;
    }
    setLocationGranted(true);
    fetchCurrentLocation();
  };

  const fetchCurrentLocation = async () => {
    try {
      let location = await Location.getCurrentPositionAsync({});
      setCurrentRegion({
        latitude: location.coords.latitude,
        longitude: location.coords.longitude,
        latitudeDelta: 0.05,
        longitudeDelta: 0.05,
      });
      setOrigin('Current Location');
    } catch (error) {
      console.log('Error fetching location', error);
    }
  };

  const handleSearch = () => {
    if (!destination) {
      Alert.alert('Please enter a destination');
      return;
    }
    onSearch({ origin, destination });
  };

  return (
    <View style={styles.container}>
      <MapView
        provider={PROVIDER_GOOGLE}
        style={styles.map}
        region={currentRegion}
        showsUserLocation={locationGranted}
        showsMyLocationButton={false}
      />

      {/* Top Search Bar Overlay */}
      <View style={styles.searchContainer}>
        <View style={styles.searchBox}>
          <TextInput
            style={styles.searchInput}
            placeholder="Search destination"
            value={destination}
            onChangeText={setDestination}
            placeholderTextColor="#9ca3af"
            onSubmitEditing={handleSearch}
            returnKeyType="search"
          />
          <Pressable style={styles.searchButton} onPress={handleSearch}>
            <Text style={{ fontSize: 18 }}>🔍</Text>
          </Pressable>
        </View>
      </View>

      {/* Floating Action Buttons */}
      <View style={styles.fabContainer}>
        <Pressable style={styles.fab} onPress={fetchCurrentLocation}>
          <Text style={{ fontSize: 20 }}>📍</Text>
        </Pressable>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  map: {
    ...StyleSheet.absoluteFillObject,
  },
  searchContainer: {
    position: 'absolute',
    top: 50, // Safe area margin
    left: 16,
    right: 16,
    zIndex: 40,
  },
  searchBox: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#ffffff',
    borderRadius: 30,
    height: 52,
    paddingLeft: 20,
    paddingRight: 6,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 12,
    elevation: 5,
  },
  searchInput: {
    flex: 1,
    height: '100%',
    fontSize: 16,
    color: '#1f2937',
    fontWeight: '500',
  },
  searchButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#f3f4f6',
    justifyContent: 'center',
    alignItems: 'center',
  },
  fabContainer: {
    position: 'absolute',
    right: 16,
    bottom: 40,
    zIndex: 20,
  },
  fab: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#ffffff',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 8,
    elevation: 4,
  },
});

export default HomeScreen;
