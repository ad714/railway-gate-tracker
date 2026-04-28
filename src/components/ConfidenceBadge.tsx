import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Confidence } from '../types/gate';

interface ConfidenceBadgeProps {
    level: Confidence;
}

const ConfidenceBadge: React.FC<ConfidenceBadgeProps> = ({ level }) => {
    const getStyles = () => {
        switch (level) {
            case 'HIGH':
                return { dot: styles.highDot, text: styles.highText, bg: styles.highBg };
            case 'MEDIUM':
                return { dot: styles.mediumDot, text: styles.mediumText, bg: styles.mediumBg };
            case 'LOW':
            default:
                return { dot: styles.lowDot, text: styles.lowText, bg: styles.lowBg };
        }
    };

    const { dot, text, bg } = getStyles();

    return (
        <View style={[styles.container, bg]}>
            <View style={[styles.dot, dot]} />
            <Text style={[styles.text, text]}>{level} Confidence</Text>
        </View>
    );
};

const styles = StyleSheet.create({
    container: {
        flexDirection: 'row',
        alignItems: 'center',
        paddingHorizontal: 8,
        paddingVertical: 4,
        borderRadius: 6,
    },
    dot: {
        width: 6,
        height: 6,
        borderRadius: 3,
        marginRight: 6,
    },
    text: {
        fontSize: 10,
        fontWeight: '600',
        textTransform: 'uppercase',
    },
    highDot: { backgroundColor: '#10b981' },
    highText: { color: '#065f46' },
    highBg: { backgroundColor: '#f0fdf4' },
    mediumDot: { backgroundColor: '#f59e0b' },
    mediumText: { color: '#92400e' },
    mediumBg: { backgroundColor: '#fffbeb' },
    lowDot: { backgroundColor: '#ef4444' },
    lowText: { color: '#991b1b' },
    lowBg: { backgroundColor: '#fef2f2' },
});

export default ConfidenceBadge;
