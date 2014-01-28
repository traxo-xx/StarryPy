import logging
from uuid import uuid4

import construct
from twisted.internet import reactor
from twisted.internet.protocol import ClientFactory, ServerFactory, Protocol, connectionDone
from construct import Container
import construct.core

from config import ConfigurationManager
from packet_stream import PacketStream
import packets
from plugin_manager import PluginManager, route
from utility_functions import build_packet


class StarryPyServerProtocol(Protocol):
    """
    The main protocol class for handling connections from Starbound clients.
    """

    def __init__(self):
        """
        """
        self.id = str(uuid4().hex)
        self.factory.protocols[self.id] = self
        self.player = None
        self.state = None
        self.config = ConfigurationManager()
        self.parsing = False
        self.buffering_packet = None
        self.after_write_callback = None
        self.plugin_manager = None
        self.debug_file = open(self.config.debug_file, 'w')
        self.call_mapping = {
            packets.Packets.PROTOCOL_VERSION: self.protocol_version,
            packets.Packets.CONNECT_RESPONSE: self.connect_response,
            packets.Packets.SERVER_DISCONNECT: self.server_disconnect,
            packets.Packets.HANDSHAKE_CHALLENGE: self.handshake_challenge,
            packets.Packets.CHAT_RECEIVED: self.chat_received,
            packets.Packets.UNIVERSE_TIME_UPDATE: self.universe_time_update,
            packets.Packets.CLIENT_CONNECT: self.client_connect,
            packets.Packets.CLIENT_DISCONNECT: self.client_disconnect,
            packets.Packets.HANDSHAKE_RESPONSE: self.handshake_response,
            packets.Packets.WARP_COMMAND: self.warp_command,
            packets.Packets.CHAT_SENT: self.chat_sent,
            packets.Packets.CLIENT_CONTEXT_UPDATE: self.client_context_update,
            packets.Packets.WORLD_START: self.world_start,
            packets.Packets.WORLD_STOP: self.world_stop,
            packets.Packets.TILE_ARRAY_UPDATE: self.tile_array_update,
            packets.Packets.TILE_UPDATE: self.tile_update,
            packets.Packets.TILE_LIQUID_UPDATE: self.tile_liquid_update,
            packets.Packets.TILE_DAMAGE_UPDATE: self.tile_damage_update,
            packets.Packets.TILE_MODIFICATION_FAILURE: self.tile_modification_failure,
            packets.Packets.GIVE_ITEM: self.give_item,
            packets.Packets.SWAP_IN_CONTAINER_RESULT: self.swap_in_container_result,
            packets.Packets.ENVIRONMENT_UPDATE: self.environment_update,
            packets.Packets.ENTITY_INTERACT_RESULT: self.entity_interact_result,
            packets.Packets.MODIFY_TILE_LIST: self.modify_tile_list,
            packets.Packets.DAMAGE_TILE: self.damage_tile,
            packets.Packets.DAMAGE_TILE_GROUP: self.damage_tile_group,
            packets.Packets.REQUEST_DROP: self.request_drop,
            packets.Packets.SPAWN_ENTITY: self.spawn_entity,
            packets.Packets.ENTITY_INTERACT: self.entity_interact,
            packets.Packets.CONNECT_WIRE: self.connect_wire,
            packets.Packets.DISCONNECT_ALL_WIRES: self.disconnect_all_wires,
            packets.Packets.OPEN_CONTAINER: self.open_container,
            packets.Packets.CLOSE_CONTAINER: self.close_container,
            packets.Packets.SWAP_IN_CONTAINER: self.swap_in_container,
            packets.Packets.ITEM_APPLY_IN_CONTAINER: self.item_apply_in_container,
            packets.Packets.START_CRAFTING_IN_CONTAINER: self.start_crafting_in_container,
            packets.Packets.STOP_CRAFTING_IN_CONTAINER: self.stop_crafting_in_container,
            packets.Packets.BURN_CONTAINER: self.burn_container,
            packets.Packets.CLEAR_CONTAINER: self.clear_container,
            packets.Packets.WORLD_UPDATE: self.world_update,
            packets.Packets.ENTITY_CREATE: self.entity_create,
            packets.Packets.ENTITY_UPDATE: self.entity_update,
            packets.Packets.ENTITY_DESTROY: self.entity_destroy,
            packets.Packets.DAMAGE_NOTIFICATION: self.damage_notification,
            packets.Packets.STATUS_EFFECT_REQUEST: self.status_effect_request,
            packets.Packets.UPDATE_WORLD_PROPERTIES: self.update_world_properties,
            packets.Packets.HEARTBEAT: self.heartbeat,
        }
        logging.info("Created StarryPyServerProtocol with UUID %s" % self.id)

    def connectionMade(self):
        """
        Called when the connection to the requesting client is actually
        established.

        After the connection is established, it attempts to connect to the
        actual starbound server using StarboundClientFactory()
        :rtype : None
        """
        self.plugin_manager = self.factory.plugin_manager
        self.packet_stream = PacketStream(self)
        self.packet_stream.direction = packets.Direction.CLIENT
        logging.debug("Connection made in StarryPyServerProtocol with UUID %s" %
                      self.id)
        reactor.connectTCP(self.config.server_hostname, self.config.server_port, StarboundClientFactory(self))

    def string_received(self, packet):
        """
        This method is called whenever a completed packet is received from the 
        client going to the Starbound server.
        This is the first and only time where these packets can be modified,
        stopped, or allowed.

        Processing of parsed data is handled in handle_starbound_packets()
        :rtype : None
        """
        if 48 >= packet.id:
            if self.handle_starbound_packets(packet):
                self.client_protocol.transport.write(
                    packet.original_data)
                if self.after_write_callback is not None:
                    self.after_write_callback()
        else:
            # We received an unknown packet; send it along.
            logging.warning(
                "Received unknown message ID (%d) from client." %
                packet.id)
            self.client_protocol.transport.write(
                packet.original_data)

    def dataReceived(self, data):
        """
        Called whenever a packet is received. Generally this should not be
        tampered with directly, as it attempts to reconstruct the packet
        that Starbound clients send out.

        The actual handling of the reconstructed packet should be done in
        string_received(), which is called when the packet is built.

        :param data: Raw packet data from Twisted.

        :rtype : None
        """
        self.packet_stream += data

    @route
    def protocol_version(self, data):
        return True

    @route
    def server_disconnect(self, data):
        return True

    @route
    def handshake_challenge(self, data):
        return True

    @route
    def chat_received(self, data):
        return True

    @route
    def universe_time_update(self, data):
        return True

    @route
    def handshake_response(self, data):
        return True

    @route
    def client_context_update(self, data):
        return True

    @route
    def world_start(self, data):
        return True

    @route
    def world_stop(self, data):
        return True

    @route
    def tile_array_update(self, data):
        return True

    @route
    def tile_update(self, data):
        return True

    @route
    def tile_liquid_update(self, data):
        return True

    @route
    def tile_damage_update(self, data):
        return True

    @route
    def tile_modification_failure(self, data):
        return True

    @route
    def give_item(self, data):
        return True

    @route
    def swap_in_container_result(self, data):
        return True

    @route
    def environment_update(self, data):
        return True

    @route
    def entity_interact_result(self, data):
        return True

    @route
    def modify_tile_list(self, data):
        return True

    @route
    def damage_tile(self, data):
        return True

    @route
    def damage_tile_group(self, data):
        return True

    @route
    def request_drop(self, data):
        return True

    @route
    def spawn_entity(self, data):
        return True

    @route
    def entity_interact(self, data):
        return True

    @route
    def connect_wire(self, data):
        return True

    @route
    def disconnect_all_wires(self, data):
        return True

    @route
    def open_container(self, data):
        return True

    @route
    def close_container(self, data):
        return True

    @route
    def swap_in_container(self, data):
        return True

    @route
    def item_apply_in_container(self, data):
        return True

    @route
    def start_crafting_in_container(self, data):
        return True

    @route
    def stop_crafting_in_container(self, data):
        return True

    @route
    def burn_container(self, data):
        return True

    @route
    def clear_container(self, data):
        return True

    @route
    def world_update(self, data):
        return True

    @route
    def entity_create(self, data):
        return True

    @route
    def entity_update(self, data):
        return True

    @route
    def entity_destroy(self, data):
        return True

    @route
    def status_effect_request(self, data):
        return True

    @route
    def update_world_properties(self, data):
        return True

    @route
    def heartbeat(self, data):
        return True

    @route
    def connect_response(self, data):
        """
        Called when the server responds to the client's connection request
        after handshaking.

        :param data: Parsed packet.
        :rtype : bool
        """
        return True

    @route
    def chat_sent(self, data):
        """
        Called when the client attempts to send a chat message/command to the
        server.

        :param data: Parsed chat packet.
        :rtype : bool
        """
        return True

    @route
    def damage_notification(self, data):
        return True

    @route
    def client_connect(self, data):
        """
        Called when the client attempts to connect to the Starbound server.

        :param data: Parsed client_connect packet.
        :rtype : bool
        """
        return True

    @route
    def client_disconnect(self, player):
        """
        Called when the client singnals that it is about to disconnect from the Starbound server.

        :param player: The Player.
        :rtype : bool
        """
        return True

    @route
    def warp_command(self, data):
        """
        Called when the players issues a warp.

        :param data: The warp_command data.
        :rtype : bool
        """
        return True

    def handle_starbound_packets(self, p):
        """
        This function is the meat of it all. Every time a full packet with
        a derived ID <= 48, it is passed through here.
        """
        return self.call_mapping[p.id](p)

    def send_chat_message(self, text, channel=0, world='', name=''):
        """
        Convenience function to send chat messages to the client. Note that this
        does *not* send messages to the server at large; broadcast should be
        used for messages to all clients, or manually constructed chat messages
        otherwise.

        :param text: Message text, may contain multiple lines.
        :param channel: The chat channel/context. 0 is global, 1 is planet.
        :param world: World
        :param name: The name to display before the message. Blank leaves no
        brackets, otherwise it will be displayed as `<name>`.
        :return: None
        """
        if '\n' in text:
            lines = text.split('\n')
            for line in lines:
                self.send_chat_message(line)
            return
        chat_data = packets.chat_received().build(Container(chat_channel=channel,
                                                            world=world,
                                                            client_id=0,
                                                            name=name,
                                                            message=unicode(text)))
        chat_packet = build_packet(packets.Packets.CHAT_RECEIVED,
                                   chat_data)
        self.transport.write(chat_packet)

    def write(self, data):
        """
        Convenience method to send data to the client.
        :param data: Data to send.
        :return: None
        """
        self.transport.write(data)

    def connectionLost(self, reason=connectionDone):
        """
        Called as a pseudo-destructor when the connection is lost.
        :param reason: The reason for the disconnection.
        :return: None
        """
        if self.player:
            if self.player.logged_in:
                try:
                    self.client_disconnect(None)
                except:
                    pass
                finally:
                    logging.warning("Lost connection. Reason given: %s" % str(reason))

    def die(self):
        self.transport.loseConnection()
        try:
            self.client_protocol.transport.loseConnection()
        except AttributeError:
            pass
        self.factory.protocols.pop(self.id, None)


class ClientProtocol(Protocol):
    """
    The protocol class which handles the connection to the Starbound server.
    """

    def __init__(self):
        self.packet_stream = PacketStream(self)
        self.packet_stream.direction = packets.Direction.SERVER

    def connectionMade(self):
        """
        Called when the connection to the Starbound server is initially
        established. Inserts a self-reference in the server_protocol to allow
        two-way communication.

        :return: None
        """
        self.server_protocol.client_protocol = self
        self.parsing = False


    def string_received(self, packet):
        """
        This method is called whenever a completed packet is received from the
        Starbound server.

        This is the first and only time where these packets can be modified,
        stopped, or allowed.

        Processing of parsed data is handled in handle_starbound_packets()

        :return: None
        """
        try:
            if self.server_protocol.handle_starbound_packets(
                    packet):
                self.server_protocol.write(
                    packet.original_data)
        except construct.core.FieldError as e:
            logging.error(str(e))
            self.server_protocol.write(
                packet.original_data)


    def dataReceived(self, data):
        """
        Called whenever a packet is received. Generally this should not be
        tampered with directly, as it attempts to reconstruct the packet
        that the Starbound server sent out.

        The actual handling of the reconstructed packet should be done in
        string_received(), which is called when the packet is built.
        :param data: Raw packet data from the Starbound server.
        :return: None
        """
        self.packet_stream += data


class StarryPyServerFactory(ServerFactory):
    """
    Factory which creates `StarryPyServerProtocol` instances.
    """
    protocol = StarryPyServerProtocol

    def __init__(self):
        """
        Initializes persistent objects and prepares a list of connected
        protocols.
        """
        self.config = ConfigurationManager()
        self.protocol.factory = self
        self.protocols = {}
        self.plugin_manager = PluginManager()
        self.plugin_manager.activate_plugins()

    def stopFactory(self):
        """
        Called when the factory is stopped. Saves the configuration.
        :return: None
        """
        self.config.save()

    def broadcast(self, text, channel=1, world='', name=''):
        """
        Convenience method to send a broadcasted message to all clients on the
        server.

        :param text: Message text
        :param channel: Channel to broadcast on. 0 is global, 1 is planet.
        :param world: World
        :param name: The name to prepend before the message, format is <name>
        :return: None
        """
        try:
            for p in self.protocols.itervalues():
                p.send_chat_message(text)
        except Exception as e:
            logging.error(e)

    def buildProtocol(self, address):
        """
        Builds the protocol to a given address.

        :rtype : Protocol
        """
        p = ServerFactory.buildProtocol(self, address)
        return p


class StarboundClientFactory(ClientFactory):
    """
    Factory which creates `StarboundClientProtocol` instances.
    """
    protocol = ClientProtocol

    def __init__(self, server_protocol):
        self.server_protocol = server_protocol

    def buildProtocol(self, address):
        protocol = ClientFactory.buildProtocol(self, address)
        protocol.server_protocol = self.server_protocol
        return protocol


if __name__ == '__main__':
    logging.basicConfig(format='[%(asctime)-15s] %(levelname)s:%(message)s', level=logging.DEBUG)
    logging.info("Started server.")
    factory = StarryPyServerFactory()
    reactor.listenTCP(21025, factory)
    reactor.run()