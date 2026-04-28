import React, { useState } from 'react';
import { View, Text, StyleSheet, SafeAreaView, FlatList, Pressable, StatusBar, Dimensions } from 'react-native';
import MapView, { Marker, Polyline, PROVIDER_GOOGLE } from 'react-native-maps';
import RouteOverviewCard from '../components/RouteOverviewCard';
import GateCard from '../components/GateCard';
import { MOCK_GATES } from '../data/mockGates';
import { RouteSummary, GateSummary } from '../types/gate';
import { COLORS, TYPOGRAPHY, SHAPES } from '../theme/tokens';

const { width, height } = Dimensions.get('window');


// Mumbai coordinates for the route
const INITIAL_REGION = {
    latitude: 19.12,
    longitude: 72.93,
    latitudeDelta: 0.15,
    longitudeDelta: 0.15,
};

// Simulating some route points for the polyline
const ROUTE_COORDINATES = [
    { latitude: 19.1176, longitude: 72.9060 }, // Powai
    { latitude: 19.1128, longitude: 72.9192 }, // Vikhroli
    { latitude: 19.1284, longitude: 72.9261 }, // Kanjurmarg
    { latitude: 19.1398, longitude: 72.9351 }, // Bhandup
    { latitude: 19.1726, longitude: 72.9444 }, // Mulund
    { latitude: 19.2045, longitude: 72.9757 }, // Thane West
];

interface RouteResultScreenProps {
    routeDetails?: { origin: string; destination: string };
    onBack?: () => void;
}

const RouteResultScreen: React.FC<RouteResultScreenProps> = ({ routeDetails, onBack }) => {
    const summary: RouteSummary = {
        origin: routeDetails?.origin || "Powai, Mumbai",
        destination: routeDetails?.destination || "Thane West",
        baseTravelTime: "45m",
        estimatedDelayRange: "15–20",
    };

    // Start with MAP mode by default for "Map-First" experience
    const [viewMode, setViewMode] = useState<'LIST' | 'MAP'>('MAP');

    const renderHeader = () => (
        <View style={styles.headerComponent}>
            <View style={styles.overviewWrapper}>
                <RouteOverviewCard summary={summary} />
            </View>

            <View style={styles.listTitleWrapper}>
                <Text style={styles.listTitle}>GATES ALONG ROUTE ({MOCK_GATES.length})</Text>
            </View>
        </View>
    );

    const getMarkerColor = (status: string) => {
        switch (status) {
            case 'LIKELY_OPEN': return COLORS.status.open;
            case 'CLOSURE_LIKELY': return COLORS.status.caution;
            case 'CLOSED': return COLORS.status.closed;
            default: return COLORS.status.uncertain;
        }
    };

    return (
        <SafeAreaView style={styles.safeArea}>
            <StatusBar barStyle="dark-content" />

            <View style={styles.mainContainer}>
                {/* Background Map - always visible in the background */}
                <View style={styles.mapContainer}>
                    <MapView
                        provider={PROVIDER_GOOGLE}
                        style={styles.map}
                        initialRegion={INITIAL_REGION}
                    >
                        <Polyline
                            coordinates={ROUTE_COORDINATES}
                            strokeColor={COLORS.secondary}
                            strokeWidth={4}
                        />
                        {MOCK_GATES.map((gate, index) => (
                            <Marker
                                key={gate.gateId}
                                coordinate={ROUTE_COORDINATES[index % ROUTE_COORDINATES.length]} // Mock positioning
                                title={gate.name}
                                description={`${gate.status.replace('_', ' ')} • ${gate.distanceAheadKm}km ahead`}
                                pinColor={getMarkerColor(gate.status)}
                            />
                        ))}
                    </MapView>
                </View>

                {/* Navbar Overlay */}
                <View style={styles.navBarFloating}>
                    <Pressable style={styles.backButton} onPress={onBack}>
                        <View style={styles.backArrow} />
                    </Pressable>
                    <Text style={styles.navTitle} numberOfLines={1}>Trip to {summary.destination}</Text>
                    
                    <View style={styles.modeToggle}>
                        <Pressable
                            onPress={() => setViewMode('LIST')}
                            style={[styles.modeTab, viewMode === 'LIST' && styles.activeTab]}
                        >
                            <Text style={[styles.modeTabText, viewMode === 'LIST' && styles.activeTabText]}>LIST</Text>
                        </Pressable>
                        <Pressable
                            onPress={() => setViewMode('MAP')}
                            style={[styles.modeTab, viewMode === 'MAP' && styles.activeTab]}
                        >
                            <Text style={[styles.modeTabText, viewMode === 'MAP' && styles.activeTabText]}>MAP</Text>
                        </Pressable>
                    </View>
                </View>

                {/* Draggable-style List Overlay */}
                <View style={[
                    styles.bottomSheetContainer, 
                    viewMode === 'LIST' ? styles.bottomSheetExpanded : styles.bottomSheetPeek
                ]}>
                    <View style={styles.sheetHandle} />
                    
                    {viewMode === 'LIST' ? (
                        <FlatList
                            data={MOCK_GATES}
                            keyExtractor={(item) => item.gateId}
                            renderItem={({ item }) => (
                                <GateCard
                                    gate={item}
                                    onPress={() => console.log('Gate pressed:', item.gateId)}
                                />
                            )}
                            ListHeaderComponent={renderHeader}
                            contentContainerStyle={styles.listContent}
                            showsVerticalScrollIndicator={false}
                        />
                    ) : (
                        <View style={styles.peekContent}>
                            <RouteOverviewCard summary={summary} />
                            <Pressable 
                                style={styles.expandButton}
                                onPress={() => setViewMode('LIST')}
                            >
                                <Text style={styles.expandButtonText}>View All Gates</Text>
                            </Pressable>
                        </View>
                    )}
                </View>

                {/* FAB Overlay */}
                {viewMode === 'MAP' && (
                    <Pressable style={styles.fab}>
                        <View style={styles.fabIcon} />
                    </Pressable>
                )}
            </View>
        </SafeAreaView>
    );
};

const styles = StyleSheet.create({
    safeArea: {
        flex: 1,
        backgroundColor: COLORS.background,
    },
    mainContainer: {
        flex: 1,
    },
    mapContainer: {
        ...StyleSheet.absoluteFillObject,
    },
    map: {
        ...StyleSheet.absoluteFillObject,
    },
    navBarFloating: {
        position: 'absolute',
        top: 10,
        left: 10,
        right: 10,
        height: 56,
        flexDirection: 'row',
        alignItems: 'center',
        paddingHorizontal: 16,
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        borderRadius: SHAPES.borderRadius * 1.5, // 12
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.1,
        shadowRadius: 12,
        elevation: SHAPES.elevation.md,
        zIndex: 10,
    },
    backButton: {
        width: 32,
        height: 32,
        justifyContent: 'center',
        alignItems: 'center',
    },
    backArrow: {
        width: 10,
        height: 10,
        borderLeftWidth: 2,
        borderBottomWidth: 2,
        borderColor: COLORS.text.primary,
        transform: [{ rotate: '45deg' }],
    },
    navTitle: {
        fontSize: TYPOGRAPHY.sizes.lg,
        fontWeight: TYPOGRAPHY.weights.bold,
        color: COLORS.text.primary,
        marginLeft: 8,
        flex: 1,
    },
    modeToggle: {
        flexDirection: 'row',
        backgroundColor: COLORS.surface,
        borderRadius: SHAPES.borderRadius,
        padding: 2,
    },
    modeTab: {
        paddingHorizontal: 10,
        paddingVertical: 5,
        borderRadius: SHAPES.borderRadius - 2,
    },
    activeTab: {
        backgroundColor: COLORS.background,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.1,
        shadowRadius: 2,
        elevation: SHAPES.elevation.sm,
    },
    modeTabText: {
        fontSize: TYPOGRAPHY.sizes.xs,
        fontWeight: TYPOGRAPHY.weights.bold,
        color: COLORS.text.secondary,
        letterSpacing: 0.5,
    },
    activeTabText: {
        color: COLORS.primary,
    },
    bottomSheetContainer: {
        position: 'absolute',
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: COLORS.background,
        borderTopLeftRadius: SHAPES.borderRadius * 3, // 24
        borderTopRightRadius: SHAPES.borderRadius * 3, // 24
        shadowColor: '#000',
        shadowOffset: { width: 0, height: -4 },
        shadowOpacity: 0.1,
        shadowRadius: 12,
        elevation: SHAPES.elevation.lg,
        zIndex: 20,
    },
    bottomSheetPeek: {
        height: 240,
    },
    bottomSheetExpanded: {
        height: '85%',
    },
    sheetHandle: {
        width: 40,
        height: 5,
        backgroundColor: COLORS.border,
        borderRadius: 3,
        alignSelf: 'center',
        marginTop: 12,
        marginBottom: 8,
    },
    peekContent: {
        padding: 16,
        flex: 1,
    },
    expandButton: {
        backgroundColor: COLORS.primary,
        paddingVertical: 14,
        borderRadius: SHAPES.borderRadius + 4,
        alignItems: 'center',
        marginTop: 16,
    },
    expandButtonText: {
        color: COLORS.text.inverse,
        fontSize: TYPOGRAPHY.sizes.base + 1,
        fontWeight: TYPOGRAPHY.weights.bold,
    },
    listContent: {
        paddingBottom: 40,
    },
    headerComponent: {
        paddingTop: 8,
        paddingBottom: 16,
    },
    overviewWrapper: {
        marginBottom: 16,
    },
    listTitleWrapper: {
        paddingHorizontal: 16,
        paddingBottom: 8,
    },
    listTitle: {
        fontSize: TYPOGRAPHY.sizes.sm,
        fontWeight: TYPOGRAPHY.weights.black,
        color: COLORS.text.secondary,
        letterSpacing: 1,
    },
    fab: {
        position: 'absolute',
        bottom: 260, // Above the peek sheet
        right: 20,
        width: 56,
        height: 56,
        borderRadius: 28,
        backgroundColor: COLORS.text.primary,
        justifyContent: 'center',
        alignItems: 'center',
        elevation: SHAPES.elevation.md + 1,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.2,
        shadowRadius: 8,
        zIndex: 15,
    },
    fabIcon: {
        width: 12,
        height: 12,
        borderRightWidth: 3,
        borderTopWidth: 3,
        borderColor: COLORS.background,
        transform: [{ rotate: '45deg' }],
        marginLeft: -4,
    },
});

export default RouteResultScreen;
