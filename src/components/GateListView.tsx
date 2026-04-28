import React from 'react';
import { View, Text, StyleSheet, FlatList } from 'react-native';
import GateCard from './GateCard';
import { GateSummary } from '../types/gate';

interface GateListViewProps {
    gates: GateSummary[];
    onGatePress?: (gateId: string) => void;
}

const GateListView: React.FC<GateListViewProps> = ({ gates, onGatePress }) => {
    return (
        <View style={styles.container}>
            <View style={styles.header}>
                <Text style={styles.title}>GATES ALONG ROUTE ({gates.length})</Text>
                <Text style={styles.actionText}>Sort by Distance</Text>
            </View>

            <FlatList
                data={gates}
                keyExtractor={(item) => item.gateId}
                renderItem={({ item }) => (
                    <GateCard
                        gate={item}
                        onPress={() => onGatePress?.(item.gateId)}
                    />
                )}
                scrollEnabled={false} // Managed by parent screen's FlatList/Header
                ListEmptyComponent={
                    <View style={styles.emptyState}>
                        <Text style={styles.emptyText}>No railway gates found on this route.</Text>
                    </View>
                }
                contentContainerStyle={styles.listContent}
            />
        </View>
    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
    },
    header: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        paddingHorizontal: 20,
        marginBottom: 8,
    },
    title: {
        fontSize: 12,
        fontWeight: '800',
        color: '#64748b',
        letterSpacing: 0.5,
    },
    actionText: {
        fontSize: 11,
        fontWeight: '700',
        color: '#4f46e5',
    },
    listContent: {
        paddingBottom: 20,
    },
    emptyState: {
        paddingVertical: 40,
        alignItems: 'center',
    },
    emptyText: {
        fontSize: 14,
        color: '#94a3b8',
        fontStyle: 'italic',
    },
});

export default GateListView;
