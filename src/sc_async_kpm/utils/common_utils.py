"""
This source file is part of an OSTIS project. For the latest info, see https://github.com/ostis-ai
Distributed under the MIT License
(See an accompanying file LICENSE or a copy at https://opensource.org/licenses/MIT)
"""

from typing import List, Optional, Union

from sc_async_client import client
from sc_async_client.constants import sc_type
from sc_async_client.constants.sc_type import ScType
from sc_async_client.models import (
    ScAddr,
    ScConstruction,
    ScLinkContent,
    ScLinkContentType,
    ScTemplate,
    ScTemplateResult,
)
from sc_async_client.models.sc_construction import ScLinkContentData

from sc_async_kpm.identifiers import CommonIdentifiers, ScAlias
from sc_async_kpm.sc_keynodes import Idtf, ScKeynodes


async def generate_nodes(*node_types: ScType) -> List[ScAddr]:
    construction = ScConstruction()
    for node_type in node_types:
        construction.generate_node(node_type)
    return await client.generate_elements(construction)


async def generate_node(node_type: ScType) -> ScAddr:
    nodes = await generate_nodes(node_type)
    return nodes[0]


async def generate_links(
    *contents: Union[str, int],
    content_type: ScLinkContentType = ScLinkContentType.STRING,
    link_type: ScType = sc_type.CONST_NODE_LINK,
) -> List[ScAddr]:
    construction = ScConstruction()
    for content in contents:
        link_content = ScLinkContent(content, content_type)
        construction.generate_link(link_type, link_content)
    return await client.generate_elements(construction)


async def generate_link(
    content: Union[str, int],
    content_type: ScLinkContentType = ScLinkContentType.STRING,
    link_type: ScType = sc_type.CONST_NODE_LINK,
) -> ScAddr:
    links = await generate_links(
        content, content_type=content_type, link_type=link_type
    )
    return links[0]


async def generate_connector(
    connector_type: ScType, src: ScAddr, trg: ScAddr
) -> ScAddr:
    connectors = await generate_connectors(connector_type, src, trg)
    return connectors[0]


async def generate_connectors(
    connector_type: ScType, src: ScAddr, *targets: ScAddr
) -> List[ScAddr]:
    construction = ScConstruction()
    for trg in targets:
        construction.generate_connector(connector_type, src, trg)
    return await client.generate_elements(construction)


async def generate_binary_relation(
    connector_type: ScType, src: ScAddr, trg: ScAddr, *relations: ScAddr
) -> ScAddr:
    construction = ScConstruction()
    construction.generate_connector(connector_type, src, trg, ScAlias.RELATION_ARC)
    for relation in relations:
        construction.generate_connector(
            sc_type.CONST_PERM_POS_ARC, relation, ScAlias.RELATION_ARC
        )
    elements = await client.generate_elements(construction)
    return elements[0]


async def generate_role_relation(
    src: ScAddr, trg: ScAddr, *rrel_nodes: ScAddr
) -> ScAddr:
    return await generate_binary_relation(
        sc_type.CONST_PERM_POS_ARC, src, trg, *rrel_nodes
    )


async def generate_non_role_relation(
    src: ScAddr, trg: ScAddr, *nrel_nodes: ScAddr
) -> ScAddr:
    return await generate_binary_relation(
        sc_type.CONST_COMMON_ARC, src, trg, *nrel_nodes
    )


async def check_connector(
    connector_type: ScType, source: ScAddr, target: ScAddr
) -> bool:
    connector = await search_connectors(source, target, connector_type)
    return bool(connector)


async def search_connector(
    source: ScAddr, target: ScAddr, connector_type: ScType
) -> ScAddr:
    connectors = await search_connectors(source, target, connector_type)
    return connectors[0] if connectors else ScAddr(0)


async def search_connectors(
    source: ScAddr, target: ScAddr, *connector_types: ScType
) -> List[ScAddr]:
    result_connectors = []
    for connector_type in connector_types:
        templ = ScTemplate()
        templ.triple(source, connector_type, target)
        results = await client.search_by_template(templ)
        result_connectors.extend(result[1] for result in results)
    return result_connectors


async def get_element_system_identifier(addr: ScAddr) -> Idtf:
    nrel_system_idtf = await ScKeynodes.get_by_idtf(
        CommonIdentifiers.NREL_SYSTEM_IDENTIFIER
    )

    templ = ScTemplate()
    templ.quintuple(
        addr,
        sc_type.VAR_COMMON_ARC,
        sc_type.VAR_NODE_LINK >> ScAlias.LINK,
        sc_type.VAR_PERM_POS_ARC,
        nrel_system_idtf,
    )
    result = await client.search_by_template(templ)
    if result:
        content_data = await get_link_content_data(result[0].get(ScAlias.LINK))
        return str(content_data)
    return ""


async def _search_relation_template(
    src: ScAddr, rel_node: ScAddr, rel_type: ScType
) -> Optional[ScTemplateResult]:
    template = ScTemplate()
    template.quintuple(
        src,
        rel_type >> ScAlias.RELATION_ARC,
        sc_type.UNKNOWN >> ScAlias.ELEMENT,
        sc_type.VAR_PERM_POS_ARC,
        rel_node,
    )
    result = await client.search_by_template(template)
    return result[0] if result else None


async def search_role_relation_template(
    src: ScAddr, rrel_node: ScAddr
) -> Optional[ScTemplateResult]:
    return await _search_relation_template(src, rrel_node, sc_type.VAR_PERM_POS_ARC)


async def search_non_role_relation_template(
    src: ScAddr, nrel_node: ScAddr
) -> Optional[ScTemplateResult]:
    return await _search_relation_template(src, nrel_node, sc_type.VAR_COMMON_ARC)


async def search_element_by_role_relation(src: ScAddr, rrel_node: ScAddr) -> ScAddr:
    search_result = await search_role_relation_template(src, rrel_node)
    return search_result.get(ScAlias.ELEMENT) if search_result else ScAddr(0)


async def search_element_by_non_role_relation(src: ScAddr, nrel_node: ScAddr) -> ScAddr:
    search_result = await search_non_role_relation_template(src, nrel_node)
    return search_result.get(ScAlias.ELEMENT) if search_result else ScAddr(0)


async def get_link_content_data(link: ScAddr) -> ScLinkContentData:
    content_part = await client.get_link_content(link)
    return content_part[0].data


async def erase_connectors(
    source: ScAddr, target: ScAddr, *connector_types: ScType
) -> bool:
    connectors = await search_connectors(source, target, *connector_types)
    return await client.erase_elements(*connectors)
