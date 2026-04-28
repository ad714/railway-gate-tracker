import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { RouteSummary } from '../types/gate';

interface RouteOverviewCardProps {
    summary: RouteSummary;
}

const RouteOverviewCard: React.FC<RouteOverviewCardProps> = ({ summary }) => {
    return (
        <View style={styles.container}>
            <View style={styles.routeHeader}>
                <View style={styles.placeInfo}>
                    <Text style={styles.label}>ORIGIN</Text>
                    <Text style={styles.placeName} numberOfLines={1}>{summary.origin}</Text>
                </View>

                <View style={styles.connector}>
                    <View style={styles.line} />
                    <View style={styles.dot} />
                </View>

                <View style={[styles.placeInfo, styles.placeInfoRight]}>
                    <Text style={[styles.label, styles.labelRight]}>DESTINATION</Text>
                    <Text style={[styles.placeName, styles.placeNameRight]} numberOfLines={1}>{summary.destination}</Text>
                </View>
            </View>

            <View style={styles.v2Content}>
                <View style={styles.delaySection}>
                    <Text style={styles.delayLabel}>ESTIMATED GATE DELAYS</Text>
                    <Text style={styles.delayValue}>~{summary.estimatedDelayRange} min</Text>
                </View>

                <View style={styles.divider} />

                <View style={styles.timeSection}>
                    <Text style={styles.timeLabel}>BASE TRAVEL TIME</Text>
                    <Text style={styles.timeValue}>{summary.baseTravelTime}</Text>
                </View>
            </View>

            <View style={styles.footer}>
                <View style={styles.liveIndicator}>
                    <View style={styles.indicatorDot} />
                    <Text style={styles.liveText}>Live Traffic Data</Text>
                </View>
            </View>
        </View>
    );
};

const styles = StyleSheet.create({
    container: {
        backgroundColor: '#4f46e5',
        borderRadius: 24,
        padding: 24,
        shadowColor: '#4f46e5',
        shadowOffset: { width: 0, height: 8 },
        shadowOpacity: 0.2,
        shadowRadius: 16,
        elevation: 8,
    },
    routeHeader: {
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: 24,
    },
    placeInfo: {
        flex: 1,
    },
    placeInfoRight: {
        alignItems: 'flex-end',
    },
    label: {
        fontSize: 9,
        fontWeight: '800',
        color: '#c7d2fe',
        letterSpacing: 1,
        marginBottom: 4,
    },
    labelRight: {
        textAlign: 'right',
    },
    placeName: {
        fontSize: 14,
        fontWeight: '700',
        color: '#ffffff',
    },
    placeNameRight: {
        textAlign: 'right',
    },
    connector: {
        width: 40,
        alignItems: 'center',
        justifyContent: 'center',
        marginHorizontal: 12,
    },
    line: {
        width: '100%',
        height: 1,
        backgroundColor: '#818cf8',
    },
    dot: {
        width: 6,
        height: 6,
        borderRadius: 3,
        backgroundColor: '#e0e7ff',
        position: 'absolute',
    },
    v2Content: {
        backgroundColor: 'rgba(255, 255, 255, 0.1)',
        borderRadius: 20,
        padding: 16,
        flexDirection: 'row',
        alignItems: 'center',
    },
    delaySection: {
        flex: 1.2,
    },
    delayLabel: {
        fontSize: 8,
        fontWeight: '800',
        color: '#c7d2fe',
        marginBottom: 4,
    },
    delayValue: {
        fontSize: 22,
        fontWeight: '900',
        color: '#fcd34d', // Amber 300
    },
    divider: {
        width: 1,
        height: 30,
        backgroundColor: 'rgba(255, 255, 255, 0.2)',
        marginHorizontal: 16,
    },
    timeSection: {
        flex: 1,
    },
    timeLabel: {
        fontSize: 8,
        fontWeight: '800',
        color: '#c7d2fe',
        marginBottom: 4,
    },
    timeValue: {
        fontSize: 18,
        fontWeight: '800',
        color: '#ffffff',
    },
    footer: {
        marginTop: 16,
        flexDirection: 'row',
        justifyContent: 'center',
    },
    liveIndicator: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 6,
    },
    indicatorDot: {
        width: 6,
        height: 6,
        borderRadius: 3,
        backgroundColor: '#4ade80',
    },
    liveText: {
        fontSize: 10,
        fontWeight: '600',
        color: '#e0e7ff',
    },
});

export default RouteOverviewCard;
