import React, { useState } from 'react';
import { SafeAreaView, StyleSheet } from 'react-native';
import RouteResultScreen from './src/screens/RouteResultScreen';
import HomeScreen from './src/screens/HomeScreen';

export default function App() {
  const [routeStarted, setRouteStarted] = useState(false);
  const [routeDetails, setRouteDetails] = useState({ origin: '', destination: '' });

  return (
    <SafeAreaView style={styles.container}>
      {routeStarted ? (
        <RouteResultScreen 
          routeDetails={routeDetails}
          onBack={() => setRouteStarted(false)} 
        />
      ) : (
        <HomeScreen 
          onSearch={(details) => {
            setRouteDetails(details);
            setRouteStarted(true);
          }} 
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#ffffff',
  },
});
