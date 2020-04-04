#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Instagram module for cloudburst """

import json
import requests
from datetime import datetime
from urllib.parse import urlencode, parse_qs
from cloudburst import vision as cbv

def instagram_query(hash, variables):
    query_url = "https://www.instagram.com/graphql/query/?{}".format(
        urlencode({
            'query_hash': hash, 
            'variables': json.dumps(variables, separators=(',', ':'))
        })
    )
    page_data = json.loads(requests.get(query_url).text)
    return page_data

def download_post(node, get_all_info=False):
    node_shortcode = node["shortcode"]
    node_typename = node["__typename"]

    # "caption_is_edited": node["caption_is_edited"],
    # "has_ranked_comments": node["has_ranked_comments"],
    # "is_ad": node["is_ad"],
    data_out = {
        "shortcode": node["shortcode"],
        "typename": node_typename,
        "display_url": node["display_url"],
        "id": node["id"],
        "caption": node["edge_media_to_caption"]["edges"],
        "comments_disabled": node["comments_disabled"],
        "likes": node["edge_media_preview_like"]["count"],
        "location": node["location"],
        "timestamp": node["taken_at_timestamp"],
        "time_string": str(datetime.fromtimestamp(node["taken_at_timestamp"])),
        "media": []
    }

    if node_typename == "GraphSidecar":
        for idx, node_sidecar in enumerate(node["edge_sidecar_to_children"]["edges"]):
            node_sidecar_typename = node_sidecar["__typename"]

            media_data = {
                "content_url": "",
                "id": node_sidecar["id"],
                "typename": node_sidecar_typename,
                "dimensions": node_sidecar["dimensions"],
                "accessibility_caption": node_sidecar["accessibility_caption"],
                "tagged_users": node_sidecar["edge_media_to_tagged_user"]["edges"]
            }
            
            if node_sidecar_typename == "GraphImage":
                node_url = node_sidecar["display_resources"][-1]["src"]
                media_data["content_url"] = node_url
                cbv.download_image(node_url, "{}_{}.jpg".format(node_shortcode, idx))
            elif node_typename == "GraphVideo":
                node_url = node["video_url"]
                media_data["content_url"] = node_url
                cbv.download_image(node_url, "{}_{}.mp4".format(node_shortcode, idx))

            data_out["media"].append(media_data)
            
    else:
        media_data = {
            "content_url": "",
            "dimensions": node["dimensions"],
            "tagged_users": node["edge_media_to_tagged_user"]["edges"]
        }

        if node_typename == "GraphImage":
            node_url = node["display_resources"][-1]["src"]
            media_data["content_url"] = node_url
            cbv.download_image(node_url, "{}.jpg".format(node_shortcode))
        elif node_typename == "GraphVideo":
            node_url = node["video_url"]
            media_data["content_url"] = node_url
            cbv.download_image(node_url, "{}.mp4".format(node_shortcode))
        
        data_out["media"].append(media_data)
        
    if get_all_info:
        with open("{}.json".format(node_shortcode), "w") as f:
            f.write(json.dumps(data_out, indent=4))

class Instagram:
    def __init__(self, username):
        # Retrieve JSON profile for user
        data_url = "https://www.instagram.com/{}/?__a=1".format(username)
        page_data = json.loads(requests.get(data_url).text)["graphql"]["user"]

        # Profile data gathered upon instantiation
        self.username = username
        self.id = page_data["id"]
        self.full_name = page_data["full_name"]
        self.biography = page_data["biography"]
        self.external_url = page_data["external_url"]  
        self.follower_count = page_data["edge_followed_by"]["count"]
        self.following_count = page_data["edge_follow"]["count"]
        self.has_ar_effects = page_data["has_ar_effects"]
        self.has_channel = page_data["has_channel"]
        self.has_blocked_viewer = page_data["has_blocked_viewer"]
        self.highlight_reel_count = page_data["highlight_reel_count"]
        self.has_requested_viewer = page_data["has_requested_viewer"]
        self.is_business_account = page_data["is_business_account"]
        self.business_category_name = page_data["business_category_name"]
        self.category_id = page_data["category_id"]
        self.is_joined_recently = page_data["is_joined_recently"]
        self.overall_category_name = page_data["overall_category_name"]
        self.is_private = page_data["is_private"]
        self.is_verified = page_data["is_verified"]
        self.profile_pic_url_hd = page_data["profile_pic_url_hd"]
        self.connected_fb_page = page_data["connected_fb_page"]
        self.media_count = instagram_query(
                "d496eb541e5c789274548bf473cc553e",
                {
                    "id": self.id, 
                    "first": 1,
                }
            )["data"]["user"]["edge_owner_to_timeline_media"]["count"]

    def download_profile_picture(self):
        cbv.download_image(self.profile_pic_url_hd, "{}.jpg".format(self.id))
    
    def download_posts(self):
        end_cursor = ""
        count = 0
        while(count < self.media_count):
            response = instagram_query(
                "d496eb541e5c789274548bf473cc553e",
                {
                    "id": self.id, 
                    "first": 50,
                    "after": end_cursor
                }
            )

            end_cursor = response["data"]["user"]["edge_owner_to_timeline_media"]["page_info"]["end_cursor"]
            edges = response["data"]["user"]["edge_owner_to_timeline_media"]["edges"]
            for node in edges:
                download_post(node["node"], True)
                count += 1