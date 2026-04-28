import React from 'react';
import { View, Text, Pressable, StyleSheet } from 'react-native';
import StatusBadge from './StatusBadge';
import ConfidenceBadge from './ConfidenceBadge';
import { GateSummary } from '../types/gate';
import { COLORS, TYPOGRAPHY, SHAPES } from '../theme/tokens';

interface GateCardProps {
    gate: GateSummary;
    onPress?: () => void;
}

const GateCard: React.FC<GateCardProps> = ({ gate, onPress }) => {
    const formatDelay = () => {
        if (!gate.expectedDelayMin) return 'No Expected Delay';
        const [min, max] = gate.expectedDelayMin;
        return `+${min}–${max} min delay`;
    };

    const formatTimeWindow = () => {
        if (!gate.timeWindow) return null;
        return `Expected: ${gate.timeWindow[0]} - ${gate.timeWindow[1]}`;
    };

    const isNoDelay = !gate.expectedDelayMin || gate.status === 'LIKELY_OPEN';

    return (
        <Pressable
            style={({ pressed }) => [
                styles.card,
                pressed && styles.pressedCard
            ]}
            onPress={onPress}
        >
            <View style={styles.header}>
                <StatusBadge status={gate.status} />
                <ConfidenceBadge level={gate.confidence} />
            </View>

            <View style={styles.content}>
                <View style={styles.delaySection}>
                    <Text style={[
                        styles.delayText,
                        isNoDelay ? styles.noDelay : styles.hasDelay
                    ]}>
                        {formatDelay()}
                    </Text>
                    {gate.timeWindow && (
                        <Text style={styles.timeWindowText}>{formatTimeWindow()}</Text>
                    )}
                </View>

                <View style={styles.infoSection}>
                    <View style={styles.nameLocality}>
                        <Text style={styles.gateName}>{gate.name}</Text>
                        <Text style={styles.locality}>{gate.locality}</Text>
                    </View>
                    <View style={styles.distanceBadge}>
                        <Text style={styles.distanceText}>{gate.distanceAheadKm}</Text>
                        <Text style={styles.distanceLabel}>KM AHEAD</Text>
                    </View>
                </View>
            </View>
        </Pressable>
    );
};

const styles = StyleSheet.create({
    card: {
        backgroundColor: COLORS.background,
        borderRadius: SHAPES.borderRadius * 2, // 16
        padding: 16,
        marginVertical: 8,
        marginHorizontal: 16,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.05,
        shadowRadius: 8,
        elevation: 3,
        borderWidth: 1,
        borderColor: COLORS.border,
    },
    pressedCard: {
        backgroundColor: COLORS.surface,
        transform: [{ scale: 0.98 }],
    },
    header: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 16,
    },
    content: {
        gap: 12,
    },
    delaySection: {
        marginBottom: 4,
    },
    delayText: {
        fontSize: TYPOGRAPHY.sizes.xl + 4, // 24
        fontWeight: TYPOGRAPHY.weights.black,
        letterSpacing: -0.5,
    },
    hasDelay: {
        color: COLORS.secondary,
    },
    noDelay: {
        color: COLORS.status.open,
    },
    timeWindowText: {
        fontSize: TYPOGRAPHY.sizes.sm,
        color: COLORS.text.secondary,
        fontWeight: TYPOGRAPHY.weights.medium,
        marginTop: 2,
    },
    infoSection: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'flex-end',
        paddingTop: 12,
        borderTopWidth: 1,
        borderTopColor: COLORS.border,
    },
    nameLocality: {
        flex: 1,
        marginRight: 12,
    },
    gateName: {
        fontSize: TYPOGRAPHY.sizes.base + 1, // 15
        fontWeight: TYPOGRAPHY.weights.bold,
        color: COLORS.text.primary,
        marginBottom: 2,
    },
    locality: {
        fontSize: TYPOGRAPHY.sizes.sm,
        color: COLORS.text.secondary,
        fontWeight: TYPOGRAPHY.weights.medium,
    },
    distanceBadge: {
        alignItems: 'center',
        backgroundColor: COLORS.surface,
        paddingHorizontal: 10,
        paddingVertical: 6,
        borderRadius: SHAPES.borderRadius,
    },
    distanceText: {
        fontSize: TYPOGRAPHY.sizes.base,
        fontWeight: TYPOGRAPHY.weights.black,
        color: COLORS.text.primary,
    },
    distanceLabel: {
        fontSize: TYPOGRAPHY.sizes.xs - 2, // 8
        fontWeight: TYPOGRAPHY.weights.black,
        color: '#94a3b8',
        marginTop: 1,
    },
});

export default GateCard;
